import subprocess
from utils import log as logger
import shutil
import re
import os 
import time
from pathlib import Path
from typing import Optional


WRT_CODE_WHITE_LIST = ['7019','6050','failed']
class WRTController:
    """_summary_
    this class is used to control wrt tool, to implement wrt log auto dump
    """
    @staticmethod
    def dump_wrt_log()->bool:
        """_summary_
        Dump wrt log 
        Returns:
            bool: _description_
        """
        logger.info("Starting 'cde dump_collect' to gather WRT logs.")
        try:
            #dump log 
            result = subprocess.run(
                r'"C:\Program Files\Intel\WRT2\cde.exe" dump_collect',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )
            if result.returncode != 0:
                logger.error(f"'dump_collect' command failed: {result.stderr.strip()}")
                return False
           
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False
        logger.info("Command executed successfully. Parsing output...")
        return True


    @staticmethod
    def copy_wrt_log_to_file(start_time:float,log_path:str = "", )->bool:
        """_summary_
        Copy all related wrt log to the specific path after testing
        Args:
            start_time (float): _description_
            log_path (str, optional): _description_. Defaults to "".

        Returns:
            bool: _description_
        """
        try:
            log_root = r"C:\OSData\SystemData\Temp\WRT2G\Log"
            all_dirs = [os.path.join(log_root, d) for d in os.listdir(log_root)
                    if os.path.isdir(os.path.join(log_root, d))]
            if not len(all_dirs):
                logger.error("No additional directories found to copy.")
                return 
            print(all_dirs)
            current_path = os.path.dirname(os.path.abspath(__file__))
            for dir in all_dirs:
                create_time = os.path.getmtime(dir)  
                if create_time >= start_time: 
                    target_path = os.path.join(current_path,log_path,os.path.basename(dir))
                    shutil.copytree(dir,target_path) 
        except Exception as ex:
            print(f"Error happen when copy wrt log! {ex}")
            return False 
        return True

    @staticmethod
    def clear_all_log()->bool:
        """ 

        Returns:
            bool: _description_
        """
        result = subprocess.run(
                r'"C:\Program Files\Intel\WRT2\cde.exe" clear_all',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )
        if result.returncode != 0:
            logger.error(f"'clear_all' command failed: {result.stderr.strip()}")
            return False
        return True
    
    @staticmethod
    def wrt_error_code_filter(log_path:str, white_list:list = [])->list[str]:
        """_summary_
        Filter the wrt code from the folder name
        Args:
            log_path (str): the path of log 

        Returns:
            str: _description_
        wrt info example : ['DESKTOP-LGJ88V6', '29-12-2025', '13-58-04', '929', '9', '6050', '0x0', '0x0', '0x0']
        """
        wrt_error_code = []
        current_path = os.path.dirname(os.path.abspath(__file__))
        print(current_path)
        log_root = os.path.join(current_path,log_path)
        print (log_root)
        all_dirs = [os.path.join(log_root, d) for d in os.listdir(log_root)
                    if os.path.isdir(os.path.join(log_root, d))]
        for dir in all_dirs:
            folder_name = Path(dir).name
            folder_info = folder_name.split('_')
            wrt_code = None
            for info in folder_info: 
                if len(info) == 4 and info.isdigit():
                    wrt_code = info
                    break
            happened_time =f'{folder_info[1]}-{folder_info[2]}' 
            if wrt_code and wrt_code not in white_list:
                wrt_error_code.append(f"Detect WRT CODE: {wrt_code} , happened time:{happened_time}") 
        return wrt_error_code
    


if __name__ == "__main__":
    #WRTController.dump_wrt_log()
    #WRTController.copy_wrt_log_to_file(start_time = 1765942988.6462076)
    print(WRTController.wrt_error_code_filter("report\Report_20251229_135610",WRT_CODE_WHITE_LIST))