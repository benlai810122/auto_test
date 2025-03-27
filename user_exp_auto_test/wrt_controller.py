from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class WRTController:
    """_summary_
    this class is used to control wrt tool, to implement wrt log auto dump
    """
    @staticmethod
    def dump_wrt_log():
        """
        dump wrt log
        """
        driver = webdriver.Chrome()
        driver.get("http://localhost:8082/")
        try:
            #button content = ' Dump & Collect '
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[text()=' Dump & Collect ']"))  
            ).click()
            time.sleep(20)
            
            #button content = ' Generate Report '
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[text()=' Generate Report ']"))  
            ).click()

            time.sleep(30)

            #button content = ' Clear History '
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[text()=' Clear History ']"))  
            ).click()

            time.sleep(5)

            driver.close()

        except:
            print("Some error happened!")
            raise Exception("")
         
if __name__ == "__main__":
    WRTController.dump_wrt_log()