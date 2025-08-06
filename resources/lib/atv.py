"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import random

import xbmc
import xbmcgui

from .common import addon, addon_path, translate
from . import playlist

monitor = xbmc.Monitor()


class MyPlayer(xbmc.Player):
    def __init__(self, video_playlist, *args, **kwargs):
        super(MyPlayer, self).__init__(*args, **kwargs)
        self.video_playlist = video_playlist
        self.play_index = -1
        self.active = True

    def play_next(self):
        if not self.active:
            return
        if self.play_index < len(self.video_playlist) - 1:
            self.play_index += 1
        else:
            self.play_index = 0
        current_video_path = self.video_playlist[self.play_index]
        xbmc.log(f"[Video Screensaver] Playing next video: {current_video_path}", level=xbmc.LOGDEBUG)
        self.play(current_video_path, windowed=True)
        self.apply_random_seek_if_needed(current_video_path)

    def onPlayBackEnded(self):
        xbmc.log("[Video Screensaver] Playback ended, playing next video.", level=xbmc.LOGDEBUG)
        self.play_next()

    def apply_random_seek_if_needed(self, video_path):
        if addon.getSettingBool("random-seek-local"):
            # Wait for player to be ready, with a timeout
            for _ in range(50):  # Try for up to 5 seconds
                if self.isPlayingVideo() and self.getTotalTime() > 0:
                    break
                xbmc.sleep(100)
            else:
                xbmc.log("[Video Screensaver] Player not ready for random seek.", level=xbmc.LOGWARNING)
                return

            try:
                duration = self.getTotalTime()
                min_duration_for_seek = addon.getSettingInt("random-seek-duration") * 60
                if duration > min_duration_for_seek:
                    seek_to = random.randint(1, int(duration) - 30) # Seek somewhere in the middle
                    self.seekTime(seek_to)
                    xbmc.log(f"[Video Screensaver] Seeking to {seek_to}s", level=xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log(f"[Video Screensaver] Error during random seek: {e}", level=xbmc.LOGERROR)

    def stop(self):
        self.active = False
        super(MyPlayer, self).stop()


class Screensaver(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.player = None
        self.video_playlist = playlist.get_playlist()

    def onInit(self):
        self.setProperty("screensaver-video-loading", "true")
        self.getControl(32502).setLabel(translate(32006))

        if self.video_playlist:
            self.setProperty("screensaver-video-loading", "false")
            self.player = MyPlayer(self.video_playlist)
            self.player.play_next()
        else:
            self.setProperty("screensaver-video-loading", "false")
            self.getControl(32503).setLabel(translate(32007))
            self.getControl(32503).setVisible(True)

    def clearAll(self):
        if self.player:
            self.player.stop()
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
