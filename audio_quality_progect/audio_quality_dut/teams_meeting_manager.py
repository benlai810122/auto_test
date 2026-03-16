"""
This file contains the class related to local video controlling
"""

import webbrowser
import time
from utils import Utils, log
import utils
from multiprocessing import Process
from pynput.keyboard import Key, Controller
from os import startfile, path
import pyautogui
import pyscreenshot as ImageGrab
import time


class MeetingControl:
    """
    responsible to control teams meeting
    """

    meeting_link = ""
    host_name = ""
    meeting_process: Process = None

    def __init__(self, meeting_link: str, teams_path: str):
        """
        init and set the local video path
        """
        self.meeting_link = meeting_link
        self.teams_path = teams_path

    def open_teams(self) -> bool:
        try:
            webbrowser.open(self.meeting_link)
            time.sleep(10) 
            Utils.taskkill("msedge.exe")
            Utils.taskkill("chrome.exe")
 
        except:
            log.info(
                "teams call configure error: Can't not open the teams call meeting link"
            )
            return False
        return True

    def join_meeting(self) -> bool:
        # Define the path to the "Join now" button image
        join_now_button_image = path.join(path.dirname(__file__), self.teams_path,'join_now_button.png')  
        # Find the position of the "Join now" button
        keyboard = Controller() 
        # Maximize teams  window
        keyboard.press(Key.cmd)
        time.sleep(0.3)
        keyboard.press(Key.up)
        time.sleep(0.3)
        keyboard.release(Key.up)
        time.sleep(0.3)
        keyboard.release(Key.cmd)
        time.sleep(5)
        try: 
            join_now_button = pyautogui.locateCenterOnScreen(
                join_now_button_image, confidence=0.6
            )
            pyautogui.click(join_now_button)

        except pyautogui.ImageNotFoundException:
            log.info(
                "teams call configure error: Can't find the join meeting button."
            )
            return False
        return True
 
    def open_camera_and_mute(self):
        keyboard = Controller()
        # open cameara
        keyboard.press(Key.ctrl)
        time.sleep(0.3)
        keyboard.press(Key.shift)
        time.sleep(0.3)
        keyboard.tap("o")
        time.sleep(0.3)
        keyboard.tap("m")
        time.sleep(0.3)
        keyboard.release(Key.ctrl)
        time.sleep(0.3)
        keyboard.release(Key.shift)

    def open_teams_and_join_meeting(self)->bool:
        self.open_teams()
        time.sleep(10)
        if not self.join_meeting():
            return False
        return True


    @staticmethod
    def end_meeting():
        keyboard = Controller()
        keyboard.tap(Key.tab)
        time.sleep(0.3)
        keyboard.tap(Key.right)
        time.sleep(0.3)
        keyboard.tap(Key.enter)
        time.sleep(0.3)
        keyboard.tap(Key.down)
        time.sleep(0.3)
        keyboard.tap(Key.enter)
        time.sleep(0.3)
        keyboard.tap(Key.tab)
        time.sleep(0.3)
        keyboard.tap(Key.enter)

    @staticmethod
    def close_teams():
        Utils.taskkill("ms-team")


# for testing
if __name__ == "__main__": 
    meetingControl = MeetingControl(
        "https://teams.microsoft.com/l/meetup-join/19%3ameeting_Njg2YTEwNDUtNTFlMy00ZDYyLWJjZDAtZDkwNGEzZjYxYjY1%40thread.v2/0?context=%7b%22Tid%22%3a%224d5ee319-c659-429d-bc2f-71fd32fb7d9f%22%2c%22Oid%22%3a%22434e345a-de7c-46e5-ac98-bcc931a80aaa%22%7d",
        "teams_call",
    )
    meetingControl.open_teams_and_join_meeting()
    time.sleep(60)
    MeetingControl.close_teams()
    