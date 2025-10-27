import subprocess
from utils import log as logger
import shutil
import re
import os

class WRTController:
    """_summary_
    this class is used to control wrt tool, to implement wrt log auto dump
    """
    @staticmethod
    def dump_wrt_log(log_path:str = "") :
        """
        dump wrt log
        """
        
        logger.info("Starting 'cde dump_collect' to gather WRT logs.")

        try:
            result = subprocess.run(
                r'"C:\Program Files\Intel\WRT2\cde.exe" dump_collect',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )
            #dump log 
            if result.returncode != 0:
                logger.error(f"'dump_collect' command failed: {result.stderr.strip()}")
                return
            
            log_root = r"C:\OSData\SystemData\Temp\WRT2G\Log"
            all_dirs = [os.path.join(log_root, d) for d in os.listdir(log_root)
                    if os.path.isdir(os.path.join(log_root, d))]
            if not len(all_dirs):
                logger.error("No additional directories found to copy.")
                return    
            dir_path = max(all_dirs, key=os.path.getmtime)
            current_path = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(current_path,log_path,os.path.basename(dir_path))
            shutil.copytree(dir_path,log_path)
            #generate report
            result = subprocess.run(
                r'"C:\Program Files\Intel\WRT2\cde.exe" generate_report',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )
            if result.returncode != 0:
                logger.error(f"'generate_report' command failed: {result.stderr.strip()}")
                return

            result = subprocess.run(
                r'"C:\Program Files\Intel\WRT2\cde.exe" clear_all',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )
            if result.returncode != 0:
                logger.error(f"'clear_all' command failed: {result.stderr.strip()}")
                return
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return 
        
        logger.info("Command executed successfully. Parsing output...")



if __name__ == "__main__":
    WRTController.dump_wrt_log(log_path = "report")