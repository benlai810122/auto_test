import subprocess
from utils import log as logger


class WRTController:
    """_summary_
    this class is used to control wrt tool, to implement wrt log auto dump
    """
    @staticmethod
    def dump_wrt_log():
        """
        dump wrt log
        """
        logger.info("Starting 'cde dump_collect' to gather WRT logs.")

        try:
            result = subprocess.run(
                r'"C:\Program Files\Intel\WRT2\cde.exe" dump_collect',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )

            if result.returncode != 0:
                logger.error(f"'dump_collect' command failed: {result.stderr.strip()}")
                return

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
    WRTController.dump_wrt_log()