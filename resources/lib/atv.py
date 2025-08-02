"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import threading
import random

import xbmc
import xbmcgui

from .common import addon, addon_path, translate
from .playlist import AtvPlaylist

monitor = xbmc.Monitor()


class Screensaver(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.active = True
        self.player = None
        self.video_playlist = AtvPlaylist().compute_playlist_array()

    def onInit(self):
        self.setProperty("screensaver-video-loading", "true")
        self.getControl(32502).setLabel(translate(32006))

        if self.video_playlist:
            self.setProperty("screensaver-video-loading", "false")
            self.player = xbmc.Player()
            threading.Thread(target=self.start_playback).start()
        else:
            self.setProperty("screensaver-video-loading", "false")
            self.getControl(32503).setLabel(translate(32007))
            self.getControl(32503).setVisible(True)

    def clearAll(self):
        self.active = False
        if self.player:
            self.player.stop()
        self.close()

    def onAction(self, action):
        self.clearAll()

    def start_playback(self):
        play_index = 0
        current_video_path = self.video_playlist[play_index]
        self.player.play(current_video_path, windowed=True)
        self.apply_random_seek_if_needed(current_video_path)

        while self.active and not monitor.abortRequested():
            monitor.waitForAbort(0.1)
            if not self.player.isPlaying() and self.active:
                if play_index < len(self.video_playlist) - 1:
                    play_index += 1
                else:
                    play_index = 0
                current_video_path = self.video_playlist[play_index]
                self.player.play(current_video_path, windowed=True)
                self.apply_random_seek_if_needed(current_video_path)

    def apply_random_seek_if_needed(self, video_path):
        if addon.getSettingBool("random-seek-local"):
            # Wait for player to be ready, with a timeout
            for _ in range(50):  # Try for up to 5 seconds
                if self.player.isPlayingVideo() and self.player.getTotalTime() > 0:
                    break
                xbmc.sleep(100)
            else:
                xbmc.log("[Video Screensaver] Player not ready for random seek.", level=xbmc.LOGWARNING)
                return

            try:
                duration = self.player.getTotalTime()
                if duration > 120:  # Only seek if video is longer than 2 minutes
                    seek_to = random.randint(1, int(duration) - 30) # Seek somewhere in the middle
                    self.player.seekTime(seek_to)
                    xbmc.log(f"[Video Screensaver] Seeking to {seek_to}s", level=xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log(f"[Video Screensaver] Error during random seek: {e}", level=xbmc.LOGERROR)


def run():
    screensaver = Screensaver(
        'screensaver-video.xml',
        addon_path,
        'default',
        '',
    )
    screensaver.doModal()
    del screensaver
