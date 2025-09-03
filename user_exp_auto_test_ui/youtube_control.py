"""
This file contains the class related to Youtube video control
before using the automatic power consumption run Youtube tast case
please set the youtube and msedge according to the oojar document
then download "Enhancer for YouTube" to set deafult video quality 
to 2160p 
"""

import time
from utils import Utils
from os import startfile,path
import webbrowser

class YoutubeControl:
    """
    responsible to play or stop  local video
    """

    link = ""

    def __init__(self, link: str):
        """
        init and set the link of youtube video
        """
        self.link = link

    def play(self):
        """
        open the specific youtube link and play video
        """
        #using the Window msedge to open the link (oojar required)
        webbrowser.get("open -a C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe %s")
        webbrowser.open(self.link)

    @staticmethod
    def Close():
        """
        Close the msedge
        """
        Utils.taskkill("msedge")


# for testing
if __name__ == "__main__":
    youtubeControl = YoutubeControl(link = "https://www.youtube.com/watch?v=CxwJrzEdw1U" )
    youtubeControl.play()
    time.sleep(10)
    youtubeControl.Close()
    
