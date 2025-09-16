"""
This file contains the class related to bluetooth devices controlling
"""

from utils import Utils
import os
import re
import wmi


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
    
    @staticmethod
    def find_headset() -> str:
        """
        responsible to find the connected headset 
        """
        cmd = (
            f"Get-PnpDevice -class AudioEndpoint |Select FriendlyName, Status |Select-string -Pattern headset"
        )
        # example of output: @{FriendlyName=Headphones (Galaxy Buds2 Pro); Status=OK}
        result = Utils.run_sync_ps_cmd(cmd)
        device = re.findall(r"(?<=FriendlyName=Headset \()(?!(?:.*Hands\-Free|.*Microsoft))(.*?)(?=\); Status=OK)", result)
        return device[0] if device else "None"
    
    @staticmethod
    def find_mouse_keyboard(type:str) -> str:
        """
        responsible to find the connected mouse or keyboard 
        """
        c = wmi.WMI()
        for device in c.Win32_PnPEntity():
            if type in str(device.Name) and 'Standard' not in str(device.Name) and 'HID' not in str(device.Name):
                return device.Name
        
        return 'None'


if __name__ == "__main__":
    #print(BluetoothControl.status_check(target="Zone", type="AudioEndpoint"))
    device = BluetoothControl.find_headset()
    print(device)
    pass
 