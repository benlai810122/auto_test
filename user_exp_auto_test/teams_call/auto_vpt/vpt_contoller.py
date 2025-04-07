'''
This file is related for the VPT teams call robot auto joining Class

'''

import pyautogui
import pyscreenshot as ImageGrab
import time
import webbrowser
from pynput.keyboard import Key, Controller
from os import startfile, path, chdir
from subprocess import Popen, PIPE, DEVNULL, TimeoutExpired
import pytesseract
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pygetwindow as gw



class VPTControl:
    '''
    responsible to ccontrol VPT teams robot joining meeting

    '''
    __email_account = "EmilyD@4y4577.onmicrosoft.com"
    __password = "OsCore1OsCore1!"

    def __init__(self,email:str = __email_account, password:str = __password ):
        """_summary_
            init the VPTContol object and set the email account and password
            if doesn't input vaule, will use the defult accound: EmilyD
        Args:
        Args:
            email (str, optional): _description_. Defaults to __email_account.
            password (str, optional): _description_. Defaults to __password.
        """
        self.__email_account = email
        self.__password = password
        

    def vpt_bot_join(self,)->bool:
        """_summary_
            Using this function to let robots join to specific teams meeting

        Returns:
            bool: _description_
        """
        window:gw.Win32Window
        windows =  gw.getWindowsWithTitle("cmd")
        window = windows[0]
        print(window)
        window.activate()
        window.moveTo(0,0)
        window.resizeTo(2560, 1200)

    
        screenshot_path = path.dirname(__file__) + "\\VPT\\"
        pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        doing_verify_flag = True
        #keep doing verify action until verification successful
        while doing_verify_flag:
            #execute the vpt program
            self.__execute_vpt()
            #screenshot
            self.__screenshot(save_path=screenshot_path)
            #analyze the pitcute to get verify code
            verify_code = self.__analyze_verify_code(picture_path = screenshot_path)
            #open the verify web page and input the verify code
            driver = webdriver.Chrome()
            driver.get("https://microsoft.com/devicelogin")
            doing_verify_flag = self.__input_verify_code(driver=driver, verify_code=verify_code)

        #input email info after inserting verify code 
        self.__input_email_info(driver=driver)
        time.sleep(5)
        pyautogui.click(x=400,y=400)
        time.sleep(5)
        keyboard = Controller()
        keyboard.tap(Key.enter)
        return True
    
    def __input_email_info(self,driver:webdriver)->bool:
        """_summary_
            input email and password info to the verify web
        Args:
            driver (webdriver): _description_

        Returns:
            bool: _description_
        """
        try:
            #email text box id = 'i0116'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "i0116"))  
            ).send_keys(self.__email_account)
            time.sleep(3)
            #confirm btn id = 'idSIButton9'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "idSIButton9"))  
            ).click()
            time.sleep(5)
            #password input id = 'i0118'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "i0118")) 
            ).send_keys(self.__password)
            time.sleep(3)
            #confirm btn id = 'idSIButton9'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "idSIButton9")) 
            ).click()
            time.sleep(5)
            #confirm btn id = 'idSIButton9'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "idSIButton9")) 
            ).click()
            driver.close()
        except:
            print('Can not input email info correctly')
            return False
        
    def __input_verify_code(self,driver:webdriver, verify_code:str)->bool:
        """_summary_

        Args:
            driver (webdriver): _description_
        """
        try:
            #verify text box id = 'otc'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "otc"))  
            ).send_keys(verify_code)
            time.sleep(3)
            #next step btn id = 'idSIButton9'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "idSIButton9")) 
            ).click()
            time.sleep(5)
        except:
            print("Some error happened!")
            raise Exception("")
                
        try:
            #check if there have any message after input error code = 'i0116'
            error_message = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "error"))  
            ).text
            if error_message != "":
                print("verify error, have to analyze the verify code again!")
                VPTControl.vpt_bot_close()
                driver.close()
                time.sleep(3)
                return True
        except:
            print("Don't have any error message, verify pass!")
            return False

    def __execute_vpt(self):
        """_summary_
        execute the vpt program 
        """
        vpt_path = path.dirname(__file__) + "\\VPT\\VPT1.0.9\\"
        # cmd = teams_call_file_path+'VideoPerformanceClient.exe profile --type gvc_3x3 --platform windows --bot --app Teams'
        chdir(vpt_path)
        p = Popen(["VideoPerformanceClient.exe", "profile", "--type", "gvc_3x3", "--platform", "windows", "--bot", "--app", " Teams"], shell=False)
        time.sleep(5)
        keyboard = Controller()
        keyboard.tap("y")
        time.sleep(10)

    def __screenshot(self,save_path:str):
        """_summary_
            screenshot and save the picture at ../VPT/specific path
        Args:
            save_path (str): _description_
            picture saving path
        """
        #snap the screen
        chdir(save_path)
        img = ImageGrab.grab()
        picture_name = "verify.png"
        img.save(picture_name, quality=90)

    def __analyze_verify_code(self,picture_path:str)->str:
        """_summary_
            analyze the verify code from the picture
        Args:
            picture_path (str): _description_
            the path of the screenshot
        Returns:
            str: _description_
            verify code
        """
        # analysis the verify code from the picture
        chdir(picture_path)
        image = Image.open('verify.png')
        custom_config = r'--oem 3 --psm 6'
        text = str(pytesseract.image_to_string(image,lang='eng',config=custom_config))
        index = text.rfind('enter the code')
        if index == -1: 
            print('verify code not found!')
            raise Exception("verify code not found!")
        verify_code = text[index+15:index+24]
        print("the verify_code is:"+verify_code)
        return verify_code


    @staticmethod
    def vpt_bot_close():
        """_summary_
            close the vpt program
        """
        cmd = "taskkill /im VideoPerformanceClient* /f"
        # start the process
        proc = Popen(cmd, stdout=None)
        # wait for process to finish
        proc.wait()
       
        

if __name__ == "__main__":
    vptControl = VPTControl()
    result = vptControl.vpt_bot_join()
    if not result:
        print("VPT teams robot join fail!")
    else:
        time.sleep(30)
    
    VPTControl.vpt_bot_close()
   