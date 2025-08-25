"""
This file contains the class related to local video or music controlling
"""

import time
from utils import Utils
from os import startfile,path
import subprocess


class VideoControl:
    """
    responsible to play or stop  local video
    """
    path = ""
    def __init__(self, path: str):
        """
        init and set the local video path
        """
        self.path = path

    def play(self):
        """
        start playing video with media player
        """
        video_path = path.dirname(__file__) + self.path
        #startfile(video_path)
        subprocess.Popen(["explorer",video_path])

    @staticmethod
    def stop_play():
        """
        Close media player
        """
        Utils.taskkill("Microsoft.Media.Player")
        Utils.taskkill("wmplayer.exe")

    


# for testing
if __name__ == "__main__":
    videoControl = VideoControl(
        "\\local_music\\test.mp3"
    )
    videoControl.play()
    time.sleep(10)
    VideoControl.stop_play()
