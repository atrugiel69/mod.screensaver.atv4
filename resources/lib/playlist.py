"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import os
from random import shuffle

import xbmc
import xbmcvfs

from .common import addon


class AtvPlaylist:
    def __init__(self, ):
        self.playlist = []

    def _scan_directory_recursively(self, base_path):
        video_extensions = ['.mp4', '.mov', '.mkv', '.avi', '.ts', '.m2ts']  # Common video extensions
        found_videos = []
        try:
            dirs, files = xbmcvfs.listdir(base_path)
            for file_name in files:
                # Ensure file_name is a string, as listdir can sometimes return unicode
                if not isinstance(file_name, str):
                    file_name = file_name.decode('utf-8', 'ignore')
                if os.path.splitext(file_name)[1].lower() in video_extensions:
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

    def compute_playlist_array(self):
        extra_folder_path = addon.getSetting("extra-local-folder")
        if extra_folder_path and xbmcvfs.exists(extra_folder_path):
            xbmc.log(f"Scanning local folder (recursively): {extra_folder_path}", level=xbmc.LOGDEBUG)
            try:
                self.playlist = self._scan_directory_recursively(extra_folder_path)
                if self.playlist:
                    shuffle(self.playlist)
                    xbmc.log(f"Found {len(self.playlist)} videos.", level=xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log(f"Error scanning or listing files in local folder: {extra_folder_path}. Error: {e}",
                         level=xbmc.LOGERROR)

        if self.playlist:
            return self.playlist
        else:
            xbmc.log("Playlist is empty. Please select a folder with videos in the addon settings.",
                     level=xbmc.LOGWARNING)
            return None
