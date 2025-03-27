"""
This file contains the class related to local video or music controlling
"""

import time
from utils import Utils
from os import startfile,path


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
        startfile(video_path)

    @staticmethod
    def stop_play():
        """
        Close media player
        """
        Utils.taskkill("Microsoft.Media.Player")

    


# for testing
if __name__ == "__main__":
    videoControl = VideoControl(
        "\\video\\ToS_1080p_23.976fps_H264_7000kbps_8bits_noHDR_2017v1.mp4"
    )
    videoControl.play()
    time.sleep(10)
    VideoControl.stop_play()
