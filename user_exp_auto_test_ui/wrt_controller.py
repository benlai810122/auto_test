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
            print(f"result = {result.stdout}")
            #copy log to the specific log path
            pattern = (
            r"Collected data folder:\s*C:[\\/]+OSData[\\/]+SystemData[\\/]+Temp[\\/]+WRT2G[\\/]+Log[\\/]+"
            r"([^\\/]+)"
            )
            file_name = re.search(pattern, result.stdout).group(1).strip().strip('\'"')
            dis_path = os.path.join(r"C:\OSData\SystemData\Temp\WRT2G\Log",file_name)
            current_path = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(current_path,log_path,file_name)
            print(f"dis_path = {dis_path}, log_path = {log_path}")
            shutil.copytree(dis_path, log_path)
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
            return ""
        
        logger.info("Command executed successfully. Parsing output...")



if __name__ == "__main__":
    WRTController.dump_wrt_log(log_path = "Report_20251016_171311")