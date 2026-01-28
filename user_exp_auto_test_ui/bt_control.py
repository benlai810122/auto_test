"""
This file contains the class related to bluetooth devices controlling
"""
from enum import Enum
from utils import Utils
import os
import re
import wmi


MOUSE_BLACK_LIST = ['Compatible Mouse']
KEYBOARD_BLACK_LIST = ['Keyboard_Filter','PS/2']

class bt_type(Enum):
    Keyboard = 'keyboard'
    Mouse = 'mouse'
 

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
    def find_mouse_keyboard(type:bt_type) -> str:
        """
        responsible to find the connected mouse or keyboard 
        """

        def device_filter_check(dev_name:str,filter:list)->bool:
            for b in filter:
                if b in dev_name:
                    return False
            return True


        c = wmi.WMI() 
        match type: 
            case bt_type.Mouse:  
                for device in c.Win32_PnPEntity():
                    if 'Mouse' in str(device.Name) and 'Standard' not in str(device.Name) and 'HID' not in str(device.Name):
                        if device_filter_check(str(device.Name),MOUSE_BLACK_LIST):
                            return device.Name
               
                    
            case bt_type.Keyboard:
                for device in c.Win32_PnPEntity():
                    if 'Keyboard' in str(device.Name) and 'Standard' not in str(device.Name) and 'HID' not in str(device.Name):
                       if device_filter_check(str(device.Name),KEYBOARD_BLACK_LIST):
                            return device.Name

        
        return 'None'


if __name__ == "__main__":
    #print(BluetoothControl.status_check(target="Zone", type="AudioEndpoint"))
    headset = BluetoothControl.find_headset()
    mouse = BluetoothControl.find_mouse_keyboard(bt_type.Mouse)
    keyboard = BluetoothControl.find_mouse_keyboard(bt_type.Keyboard)
    print(f'{headset} {mouse} {keyboard}')
    pass
 