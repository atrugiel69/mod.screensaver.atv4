"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import json
import os
import tarfile
from random import shuffle
from urllib import request

import xbmc
import xbmcvfs

from .commonatv import addon, addon_path, find_ranked_key_in_dict, compute_block_key_list

# Apple's URL of the resources.tar file containing entries.json
apple_resources_tar_url = "http://sylvan.apple.com/Aerials/resources-15.tar"

# Local temporary save location of the Apple TAR file
apple_local_tar_path = os.path.join(addon_path, "resources.tar")

# Local save location of the entries.json file containing video URLs
local_entries_json_path = os.path.join(addon_path, "resources", "entries.json")


# Fetch the TAR file containing the latest entries.json and overwrite the local copy
def get_latest_entries_from_apple():
    xbmc.log("Downloading the Apple Aerials resources.tar to disk", level=xbmc.LOGDEBUG)

    # Alternatively, just use the HTTP link instead of HTTPS to download the TAR locally
    request.urlretrieve(apple_resources_tar_url, apple_local_tar_path)
    # https://www.tutorialspoint.com/How-are-files-extracted-from-a-tar-file-using-Python
    apple_tar = tarfile.open(apple_local_tar_path)
    xbmc.log("Extracting entries.json from resources.tar and placing in ./resources", level=xbmc.LOGDEBUG)
    apple_tar.extract("entries.json", os.path.join(addon_path, "resources"))

    apple_tar.close()
    xbmc.log("Deleting resources.tar now that we've grabbed entries.json from it", level=xbmc.LOGDEBUG)
    os.remove(apple_local_tar_path)


class AtvPlaylist:
    def __init__(self, ):
        self.playlist = []
        self.top_level_json = {} # Initialize to empty dict
        # Set a class variable as the Bool response of our Setting.
        self.force_offline = addon.getSettingBool("force-offline")
        self.extra_local_folder_only = addon.getSettingBool("only-extra-local-folder")
        extra_folder_path = addon.getSetting("extra-local-folder")

        # Only try to load Apple's JSON if we're not in "extra local folder only" mode
        # and a valid extra local folder is actually provided.
        # Or if "extra local folder only" is selected but no valid path is given (fallback to Apple)
        should_load_apple_json = not (self.extra_local_folder_only and extra_folder_path and xbmcvfs.exists(extra_folder_path))

        if should_load_apple_json:
            if not xbmc.getCondVisibility("Player.HasMedia"):
                # If we're not forcing offline state and not using custom JSON:
                if not self.force_offline and addon.getSettingBool("get-videos-from-apple"):
                    try:
                        # Update local JSON with the copy from Apple
                        get_latest_entries_from_apple()
                    except Exception:
                        # If we hit an exception: ignore, log, and continue
                        xbmc.log(msg="Caught an exception while retrieving Apple's resources.tar to extract entries.json",
                                 level=xbmc.LOGWARNING)
                # Regardless of if we grabbed new Apple JSON, hit an exception, or are in offline mode, load the local copy
                # Also ensure the local_entries_json_path exists before trying to open it
                if xbmcvfs.exists(local_entries_json_path):
                    with open(local_entries_json_path, "r") as f:
                        self.top_level_json = json.loads(f.read())
                else:
                    xbmc.log(msg="Local entries.json not found at {}".format(local_entries_json_path), level=xbmc.LOGWARNING)
            # If Player.HasMedia, top_level_json remains empty as per original logic
        else:
            xbmc.log("Skipping Apple JSON load due to 'only-extra-local-folder' setting and valid path.", level=xbmc.LOGDEBUG)

    def _scan_directory_recursively(self, base_path):
        video_extensions = ['.mp4', '.mov', '.mkv', '.avi', '.ts', '.m2ts'] # Common video extensions
        found_videos = []
        try:
            dirs, files = xbmcvfs.listdir(base_path)
            for file_name in files:
                # Ensure file_name is a string, as listdir can sometimes return unicode
                if not isinstance(file_name, str):
                    file_name = file_name.decode('utf-8', 'ignore')
                if os.path.splitext(file_name)[1].lower() in video_extensions:
                    # xbmcvfs.listdir returns names, not full paths. Need to join.
                    # Ensure base_path also doesn't have trailing slash issues with os.join
                    # However, Kodi paths are usually well-formed with xbmcvfs.
                    full_path = os.path.join(base_path, file_name)
                    found_videos.append(full_path)
            
            for dir_name in dirs:
                # Ensure dir_name is a string
                if not isinstance(dir_name, str):
                    dir_name = dir_name.decode('utf-8', 'ignore')
                # Construct full path for subdirectory
                sub_dir_path = os.path.join(base_path, dir_name)
                # Recursive call
                found_videos.extend(self._scan_directory_recursively(sub_dir_path))
        except Exception as e:
            xbmc.log(f"Error during recursive scan of {base_path}: {e}", level=xbmc.LOGERROR)
        return found_videos

    def get_playlist_json(self):
        return self.top_level_json

    def compute_playlist_array(self):
        extra_folder_path = addon.getSetting("extra-local-folder")
        # Determine if we should exclusively use the extra local folder
        use_only_extra_local = self.extra_local_folder_only and extra_folder_path and xbmcvfs.exists(extra_folder_path)

        if not use_only_extra_local and self.top_level_json:
            # Parse the H264, HDR, and 4K settings to determine URL preference.
            block_key_list = compute_block_key_list(addon.getSettingBool("enable-4k"),
                                                    addon.getSettingBool("enable-hdr"),
                                                    addon.getSettingBool("enable-hevc"))

            # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in "assets"
            for block in self.top_level_json["assets"]:
                # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
                # Retrieve the location name
                location = block["accessibilityLabel"]
                try:
                    # Get the corresponding setting Bool by adding "enable-" + lowercase + no whitespace
                    current_location_enabled = addon.getSettingBool("enable-" + location.lower().replace(" ", ""))
                except TypeError:
                    xbmc.log("Location {} did not have a matching enable/disable setting".format(location),
                             level=xbmc.LOGDEBUG)
                    # Leave the location in the rotation if we couldn't find a corresponding setting disabling it
                    current_location_enabled = True

                # Skip the rest of the loop if the current block's location setting has been explicitly disabled
                if not current_location_enabled:
                    continue

                # Get the URL from the current block to download
                url = find_ranked_key_in_dict(block, block_key_list)

                # If the URL is empty/None, skip the rest of the loop
                if not url:
                    continue

                # If the URL contains HTTPS, we need revert to HTTP to avoid bad SSL cert
                # NOTE: Old Apple URLs were HTTP, new URLs are HTTPS with a bad cert
                if "https" in url:
                    url = url.replace("https://", "http://")

                # Get just the file's name, without the Apple HTTP URL part
                file_name = url.split("/")[-1]

                # By default, we assume a local copy of the file doesn't exist
                exists_on_disk = False
                # Inspect the disk to see if the file exists in the download location
                local_download_path = addon.getSetting("download-folder")
                if local_download_path and xbmcvfs.exists(local_download_path):
                    local_file_path = os.path.join(local_download_path, file_name)
                    if xbmcvfs.exists(local_file_path):
                        # Mark that the file exists on disk
                        exists_on_disk = True
                        # Overwrite the network URL with the local path to the file
                        url = local_file_path
                        xbmc.log("Video available locally (download folder), path is: {}".format(local_file_path), level=xbmc.LOGDEBUG)

                # If the file exists locally or we're not in offline mode, add it to the playlist
                if exists_on_disk or not self.force_offline:
                    xbmc.log("Adding Apple video for location {} to playlist".format(location), level=xbmc.LOGDEBUG)
                    self.playlist.append(url)

            # Shuffle after adding Apple's videos if any were added
            if self.playlist:
                shuffle(self.playlist)

        # Add files from the extra local folder
        # This part runs if 'use_only_extra_local' is true, or if it's false and we're mixing.
        extra_folder_path = addon.getSetting("extra-local-folder")
        if extra_folder_path and xbmcvfs.exists(extra_folder_path):
            xbmc.log(f"Scanning extra local folder (recursively): {extra_folder_path}", level=xbmc.LOGDEBUG)
            try:
                local_videos_found = self._scan_directory_recursively(extra_folder_path)
                if local_videos_found:
                    for video_path in local_videos_found:
                        if video_path not in self.playlist:
                            self.playlist.append(video_path)
                            xbmc.log(f"Added local video to playlist: {video_path}", level=xbmc.LOGDEBUG)
                    if self.playlist: # Shuffle if any videos are present (Apple's or local)
                        shuffle(self.playlist)
            except Exception as e:
                xbmc.log(f"Error scanning or listing files in extra local folder: {extra_folder_path}. Error: {e}", level=xbmc.LOGERROR)

        if self.playlist:
            return self.playlist
        else:
            # If after all attempts the playlist is empty, return None.
            # This could happen if no Apple videos were found/selected and no valid local folder/videos were provided.
            xbmc.log("Playlist is empty after attempting to populate from all sources.", level=xbmc.LOGWARNING)
            return None
