"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import threading
import random # Added for random seek
import os # Added for path comparison

import xbmc
import xbmcgui

from .commonatv import translate, addon, addon_path
from .playlist import AtvPlaylist

monitor = xbmc.Monitor()


class Screensaver(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.active = True
        self.atv4player = None
        self.video_playlist = AtvPlaylist().compute_playlist_array()

    def onInit(self):
        self.setProperty("screensaver-atv4-loading", "true")

        if self.video_playlist:
            self.setProperty("screensaver-atv4-loading", "false")
            self.atv4player = xbmc.Player()

            # Start player thread
            threading.Thread(target=self.start_playback).start()
        else:
            self.novideos()

    def novideos(self):
        self.setProperty("screensaver-atv4-loading", "false")
        self.getControl(32503).setLabel(translate(32048))
        self.getControl(32503).setVisible(True)

    def clearAll(self, close=True):
        self.active = False
        if self.atv4player:
            self.atv4player.stop()
        self.close()

    def onAction(self, action):
        self.clearAll()

    def start_playback(self):
        self.playindex = 0
        current_video_path = self.video_playlist[self.playindex]
        self.atv4player.play(current_video_path, windowed=True)
        self.apply_random_seek_if_needed(current_video_path)

        while self.active and not monitor.abortRequested():
            monitor.waitForAbort(0.1) # Shorter wait for more responsive check
            # If we finish playing the video
            if not self.atv4player.isPlaying() and self.active:
                # Increment the iterator used to access the array or reset to 0
                if self.playindex < len(self.video_playlist) - 1:
                    self.playindex += 1
                else:
                    self.playindex = 0
                # Using the updated iterator, start playing the next video
                current_video_path = self.video_playlist[self.playindex]
                self.atv4player.play(current_video_path, windowed=True)
                self.apply_random_seek_if_needed(current_video_path)

    def apply_random_seek_if_needed(self, video_path):
        if addon.getSettingBool("random-seek-local"):
            extra_folder = addon.getSetting("extra-local-folder")
            # Check if the video_path starts with the extra_folder path
            # Normalize paths to account for potential differences (e.g., trailing slashes)
            if extra_folder and video_path.startswith(os.path.normpath(extra_folder)):
                xbmc.log(f"[Aerial Screensaver] Random seek enabled for local file: {video_path}", level=xbmc.LOGDEBUG)

                # Wait for player to be ready, with a timeout
                for _ in range(50): # Try for up to 5 seconds (50 * 100ms)
                    if self.atv4player.isPlayingVideo() and self.atv4player.getTotalTime() > 0:
                        break
                    xbmc.sleep(100)
                else:
                    xbmc.log("[Aerial Screensaver] Player not ready or video duration is 0 for random seek.", level=xbmc.LOGWARNING)
                    return

                try:
                    duration = self.atv4player.getTotalTime()
                    xbmc.log(f"[Aerial Screensaver] Video duration: {duration}s", level=xbmc.LOGDEBUG)
                    min_duration_for_seek = addon.getSettingInt("random-seek-duration") * 60
                    if duration > min_duration_for_seek:
                        # Seek to a random point, but not too close to the end (e.g., leave last 5s)
                        # And not too close to the beginning (e.g., start after first 1s)
                        seek_end_margin = 5
                        if duration <= seek_end_margin * 2: # very short video, play from near start
                            seek_to = random.randint(1, int(duration) -1 if duration > 1 else 1)
                        else:
                            seek_to = random.randint(1, int(duration) - seek_end_margin)

                        self.atv4player.seekTime(seek_to)
                        xbmc.log(f"[Aerial Screensaver] Seeking to {seek_to}s", level=xbmc.LOGDEBUG)
                    else:
                        xbmc.log("[Aerial Screensaver] Video too short for random seek.", level=xbmc.LOGDEBUG)
                except Exception as e:
                    xbmc.log(f"[Aerial Screensaver] Error during random seek: {e}", level=xbmc.LOGERROR)


def run(params=False):
    if not params:
        screensaver = Screensaver(
            'screensaver-atv4.xml',
            addon_path,
            'default',
            '',
        )
        screensaver.doModal()
        del screensaver
