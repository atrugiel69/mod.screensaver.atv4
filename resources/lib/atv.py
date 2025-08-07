"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import random
import threading

import xbmc
import xbmcgui

from .common import addon, addon_path, translate
from . import playlist

monitor = xbmc.Monitor()


class Screensaver(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.player = None
        self.video_playlist = playlist.get_playlist()
        self.playback_thread = None
        self.active = True

    def onInit(self):
        self.setProperty("screensaver-video-loading", "true")
        self.getControl(32502).setLabel(translate(32006))

        if self.video_playlist:
            self.setProperty("screensaver-video-loading", "false")
            self.player = xbmc.Player()
            self.playback_thread = threading.Thread(target=self.start_playback)
            self.playback_thread.start()
        else:
            self.setProperty("screensaver-video-loading", "false")
            self.getControl(32503).setLabel(translate(32007))
            self.getControl(32503).setVisible(True)

    def start_playback(self):
        play_index = 0
        current_video_path = self.video_playlist[play_index]
        self.player.play(current_video_path, windowed=True)

        while self.active and not monitor.abortRequested():
            monitor.waitForAbort(0.1) # Shorter wait for more responsive check
            # If we finish playing the video
            if not self.player.isPlaying() and self.active:
                # Increment the iterator used to access the array or reset to 0
                if play_index < len(self.video_playlist) - 1:
                    play_index += 1
                else:
                    play_index = 0
                # Using the updated iterator, start playing the next video
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
                min_duration_for_seek = addon.getSettingInt("random-seek-duration") * 60
                if duration > min_duration_for_seek:
                    seek_to = random.randint(1, int(duration) - 30) # Seek somewhere in the middle
                    self.player.seekTime(seek_to)
                    xbmc.log(f"[Video Screensaver] Seeking to {seek_to}s", level=xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log(f"[Video Screensaver] Error during random seek: {e}", level=xbmc.LOGERROR)

    def clearAll(self):
        self.active = False
        if self.player:
            self.player.stop()
        if self.playback_thread:
            self.playback_thread.join()
        self.close()

    def onAction(self, action):
        self.clearAll()


def run():
    screensaver = Screensaver(
        'screensaver-video.xml',
        addon_path,
        'default',
        '',
    )
    screensaver.doModal()
    del screensaver
