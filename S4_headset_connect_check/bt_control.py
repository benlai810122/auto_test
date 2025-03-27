"""
This file contains the class related to bluetooth devices controlling
"""

from utils import Utils
import os
import re


class BluetoothControl:
    """
    responsible to control bluetooth devices behavior
    """

 
    @staticmethod
    def disconnect_device(target_name: str) -> str:
        """
        responsible to connect specific bluetooth device
        #Need to install "Bluetooth Command Line Tools" before using "btpair" cmd at powershell
        """

        cmd = "btpair -u -n" + target_name
        result = Utils.run_sync_ps_cmd(cmd)
        return result

    @staticmethod
    def connect_device(target_name: str, target_addr: str) -> str:
        """
        responsible to disconnect specific bluetooth device
        #Need to install "Bluetooth Command Line Tools" before using "btpair" cmd at powershell
        """
        cmd = "btpair -p -n" + target_name
        result = Utils.run_sync_ps_cmd(cmd)
        return result

    @staticmethod
    def status_check(target: str, type: str) -> bool:
        """
        responsible to check the connecting status of specific bluetooth device
        """
        cmd = (
            f"Get-PnpDevice -class {type} |Select FriendlyName, Status |Select-string -Pattern '"
            + target
            + "'"
        )
        # example of output: @{FriendlyName=Headphones (Galaxy Buds2 Pro); Status=OK}
        result = Utils.run_sync_ps_cmd(cmd)
        if match := re.findall(r"Status=(\w+)", result):
            for status in match:
                if status == "OK":
                    return True
            return False
        return False


if __name__ == "__main__":
    print(BluetoothControl.status_check(target="Dell WL7024 Headset", type="AudioEndpoint"))
 