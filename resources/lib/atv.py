import threading
import xbmc
import xbmcgui

monitor = xbmc.Monitor()

class Screensaver(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.player = None
        self.video_playlist = [
            "/storage/LinuxMedia/Aerial Screensaver Personal/TEST/comp_GMT329_113NC_396B_1105_ITALY_v03_SDR_FINAL_20180706_FRC240fps_sdr_4k_qp21_240p_t2160_tsa.mov",
            "/storage/LinuxMedia/Aerial Screensaver Personal/TEST/comp_A083_C002_1130KZ_v04_SDR_PS_FINAL_20180725_240fps_8572bbed-c0af-4af1-b604-d272a4253d3aq13_sRGB_tsa.mov"
        ]
        self.playback_thread = None
        self.active = True

    def onInit(self):
        self.player = xbmc.Player()
        self.playback_thread = threading.Thread(target=self.start_playback)
        self.playback_thread.start()

    def start_playback(self):
        play_index = 0
        self.player.play(self.video_playlist[play_index], windowed=True)

        while self.active and not monitor.abortRequested():
            monitor.waitForAbort(0.1)
            if not self.player.isPlaying() and self.active:
                if play_index < len(self.video_playlist) - 1:
                    play_index += 1
                else:
                    play_index = 0
                self.player.play(self.video_playlist[play_index], windowed=True)

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
    # We need a dummy addon object for the path
    class DummyAddon:
        def getAddonInfo(self, id):
            if id == 'path':
                return '/storage/.kodi/addons/screensaver.atv4' # This needs to be the actual path
            return ''

    addon = DummyAddon()
    addon_path = addon.getAddonInfo('path')

    screensaver = Screensaver(
        'screensaver-video.xml',
        addon_path,
        'default',
        ''
    )
    screensaver.doModal()
    del screensaver
