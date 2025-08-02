"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import xbmcaddon

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo("path")


def translate(text):
    return addon.getLocalizedString(text)
