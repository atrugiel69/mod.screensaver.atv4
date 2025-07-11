"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import xbmc
import xbmcgui

from .commonatv import translate, addon, addon_path, notification
from .trans import ScreensaverTrans


class ScreensaverPreview(xbmcgui.WindowXMLDialog):
    @staticmethod
    class ExitMonitor(xbmc.Monitor):

        def __init__(self, exit_callback):
            self.exit_callback = exit_callback

        def onScreensaverDeactivated(self):
            self.exit_callback()

    def onInit(self):
        self.exit_monitor = self.ExitMonitor(self.exit)
        self.getControl(32502).setLabel(translate(32025))
        self.setProperty("screensaver-atv4-loading", "1")
        self.exit_monitor.waitForAbort(0.2)
        self.send_input()

    @staticmethod
    def send_input():
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Input.ContextMenu", "id": 1}')

    @staticmethod
    def runAddon():
        xbmc.executebuiltin('RunAddon(screensaver.atv4)')

    def exit(self):
        self.clearProperty("screensaver-atv4-loading")
        self.close()
        # Call the script and die
        self.runAddon()


def run():
    if not xbmc.getCondVisibility("Player.HasMedia"):
        # The 'is_locked' check has been removed.
        # The settings "show-notifications" and "show-previewwindow" were removed from settings.xml.
        # For now, we will default to the behavior that was previously under 'else'
        # (i.e., not showing notifications or preview window, directly running the addon).
        # This part might need further review if notifications or a preview window are desired
        # for the local-only screensaver, which would require adding new settings.

        # Defaulting to direct addon run, similar to the old 'else' branch of the 'is_locked' check,
        # and also similar to when 'show-previewwindow' was false.
        ScreensaverPreview.ExitMonitor(ScreensaverPreview.runAddon())
        ScreensaverPreview.send_input()

        # The transparent placeholder logic (old 'else' of 'is_locked') is removed for now,
        # as 'is_locked' itself is removed. If a scenario where a transparent placeholder
        # is needed arises, it would have to be re-evaluated.
    else:
        # Just call deactivate
        ScreensaverPreview.send_input()
