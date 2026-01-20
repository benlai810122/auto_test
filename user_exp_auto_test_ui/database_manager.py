
from dataclasses import dataclass, asdict
import yaml
import requests
from utils import Utils
import re 
import subprocess
import subprocess
import platform  # For cross-platform compatibility
from typing import Optional
from pathlib import Path
import shutil
import winreg

@dataclass
class Database_data:
    op_name: str = "Tony"
    date: str = ""
    serial_num: str = ""
    os_version: str = "22631.5472"
    platform_brand: str = "HP"
    platform: str = "Regis"
    platform_phase: str = "PV"
    platform_bios: str = "123.123.123"
    cpu: str = "LNL"
    wlan: str = "BE211"
    wlan_phase: str = "B0"
    bt_driver: str = "23.165.0.3"
    bt_interface: str = "PCIe"
    wifi_driver: str = "23.140.0.5"
    audio_driver: str = "23.10.49561.1"
    wrt_version: str = "23.160.0.1"
    wrt_preset: str = "Enif"
    msft_teams_version: str = "25153.1010.3727.5483"
    scenario: str = ""
    mouse_bt: str = ""
    mouse_brand: str = ""
    mouse: str = ""
    mouse_click_period: str = ""
    keyboard_bt: str = ""
    keyboard_brand: str = ""
    keyboard: str = ""
    keyboard_click_period: str = ""
    headset_bt: str = ""
    headset_brand: str = ""
    headset: str = ""
    speaker_bt: str = ""
    speaker_brand: str = ""
    speaker: str = ""
    phone_brand: str = ""
    phone: str = ""
    device1_brand: str = ""
    device1: str = ""
    modern_standby: str = ""
    ms_period: str = ""
    ms_os_waiting_time: str = ""
    s4: str = ""
    s4_period: str = ""
    s4_os_waiting_time: str = ""
    warm_boot: str = ""
    wb_period: str = ""
    wb_os_waiting_time: str = ""
    cold_boot: str = ""
    cb_period: str = ""
    cb_os_waiting_time: str = ""
    microsoft_teams: str = ""
    apm: str = ""
    apm_period: str = ""
    opp: str = ""
    swift_pair: str = ""
    power_type: str = "AC"
    urgent_level: str = "P2"
    fix_work_week: str = ""
    fix_bt_driver: str = ""
    jira_id: str = ""
    ips_id: str = ""
    hsd_id: str = ""
    result: str = ""
    fail_cycles: str = ""
    cycles: str = ""
    duration: str = ""
    log_path: str = ""
    sys_event_log: str = ""
    wifi_name:str = ""
    wifi_band:str = ""
    comment:str = ""


IP = "192.168.70.122"
BASE_URL = f"http://{IP}:8001"
DRIVER_BT = "Intel(R) Wireless Bluetooth(R)"
DRIVER_BT_DUAL = "Intel(R) Wireless Dual Bluetooth(R)"
DRIVER_WIFI = "Intel(R) Wi-Fi"
DRIVER_ISST = "Smart Sound Technology for Bluetooth"
DRIVER_WLAN = "wlan"

def ensure_database_setting():
    cfg = Path("database_data.yaml")
    template = Path("database_data.yaml.example")

    if not cfg.exists():
        shutil.copy(template, cfg)
        print("Created database_data.yaml from template")
    else:
        print("Using existing database_data.yaml")

def load_database_data(file_path: str) -> Database_data:
    #load the database data from yaml file
    with open(file_path) as f:
        data = yaml.safe_load(f)
    return Database_data(**data)

def database_data_checking(ori_data:Database_data, nec_data_array:list[str])->bool:
    #check the necessary daata won't be Null
    for data in nec_data_array:
        if getattr(ori_data,data) == "":
            return False  
    return True
    
def test_create_report(payload)->int:
    #update the data to the database
    response = requests.post(f"{BASE_URL}/reports/script", json=payload) 
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200
    return response.json()["id"]

def server_available_checked(IP:str)->bool:
    """
    Pings a host and returns True if the host is up, False otherwise.
    """
    # Option for the number of packets: use '-n 1' for Windows or '-c 1' for Linux/macOS
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Building the command list
    command = ['ping', param, '1', IP]  # Only send 1 packet and wait a short time

    # Execute the command and check the return code
    # subprocess.call returns 0 for success
    try:
        # We can use subprocess.DEVNULL to suppress the ping output to the console
        result = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result == 0:
            return True
        else:
            return False
    except FileNotFoundError:
        print(f"Error: The 'ping' command was not found. Check your system's PATH.")
        return False
    
    return True


def get_serial_number()->str:
    serial = ""
    cmd = 'Get-CimInstance Win32_BIOS | Select-Object SerialNumber'
    result = Utils.run_sync_ps_cmd(cmd)
    match = re.search(r"SerialNumber\s*-+\s*([A-Z0-9]+)", result)
    if match:
        serial = match.group(1)
    print(f"Serial numble = {serial}")
    return serial

def get_driver_versions():
    #get wifi, bluetooth and isst driver version, also the wlan
    output = subprocess.check_output(
        ["wmic", "path", "Win32_PnPSignedDriver", "get", "DeviceName,DriverVersion"],
        shell=False
    ).decode("utf-8", errors="ignore") 
    results = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("DeviceName"):
            continue
        if (DRIVER_BT in line):
            # split from the right: name .... version
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                name, version = parts
                results[DRIVER_BT] = version.strip()
        if (DRIVER_BT_DUAL in line):
            # split from the right: name .... version
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                name, version = parts
                results[DRIVER_BT_DUAL] = version.strip()
        elif (DRIVER_WIFI in line):
            # split from the right: name .... version
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                name, version = parts
                results[DRIVER_WIFI] = version.strip()

                # also add the wlan
                match = re.search(r"(AX\d{3}|BE\d{3}|AC\d{4}|AC\d{3}|\b[89]\d{3}\b)", name, re.IGNORECASE)
                if match:
                    results[DRIVER_WLAN] = match.group(0).upper()
        
        elif (DRIVER_ISST in line):
            # split from the right: name .... version
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                name, version = parts
                results[DRIVER_ISST] = version.strip()

    return results

def get_bios_version():
    cmd = ["wmic", "bios", "get", "smbiosbiosversion"]
    output = subprocess.check_output(cmd, shell=False).decode("utf-8", errors="ignore")
    lines = [line.strip() for line in output.splitlines() if line.strip() and "SMBIOSBIOSVersion" not in line]
    return lines[0] if lines else None

def get_platform_brand():
    cmd = ["wmic", "csproduct", "get", "vendor"]
    output = subprocess.check_output(cmd, shell=False).decode(errors="ignore")
    lines = [l.strip() for l in output.splitlines() if l.strip() and "Vendor" not in l]
    return lines[0] if lines else None

def get_platform_name():
    cmd = ["wmic", "csproduct", "get", "name"]
    output = subprocess.check_output(cmd, shell=False).decode("utf-8", errors="ignore")
    lines = [l.strip() for l in output.splitlines() if l.strip() and "Name" not in l]
    return lines[0] if lines else None

def get_os_version():
    #get os version with UBR
    key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
        current_build = winreg.QueryValueEx(key, "CurrentBuild")[0]
        ubr = winreg.QueryValueEx(key, "UBR")[0]  # <-- this is .7535
    return f"{current_build}.{ubr}"

def get_cpu_name():
    cmd = ["wmic", "cpu", "get", "name"]
    output = subprocess.check_output(cmd, shell=False).decode("utf-8", errors="ignore")
    lines = [l.strip() for l in output.splitlines() if l.strip() and "Name" not in l]
    return lines[0] if lines else None

def get_teams_version():
    cmd = [
        "powershell",
        "(Get-AppxPackage -Name 'MSTeams' | Select-Object -ExpandProperty Version)"
    ]
    try:
        output = subprocess.check_output(cmd, shell=False).decode("utf-8").strip()
        return output if output else None
    except:
        return None
    
def get_connected_wifi_name() -> str:
    """
    Returns the connected Wi-Fi SSID on Windows, or OFF if not connected / not found.
    """
    try: 
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'OFF'
 
    m = re.search(r"^\s*SSID\s*:\s*(.+?)\s*$", out, flags=re.MULTILINE)
    if not m:
        return 'OFF' 
    ssid = m.group(1).strip() 
    return ssid if ssid else 'OFF'

def get_connected_wifi_band() -> str:
    """
    Returns the connected Wi-Fi band on Windows, or OFF if not connected / not found.
    """
    try: 
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'OFF' 
    bands = [b.strip() for b in re.findall(r"\bBand\s*:\s*([^,\r\n]+)", out)]
    if not len(bands):
        return 'OFF'  
    return bands[-1]

def get_wrt_version_and_preset() -> Optional[dict]:
    """_summary_
    
    Returns:
        dict: [ver] = wrt version
              [present] = wrt preset
    """
    try:  
        out = subprocess.check_output(
            ["C:\Program Files\Intel\WRT2\cde.exe", "system_info"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        wrt_m = re.search(r'"WRT::2G Version"\s*:\s*"([^"]+)"', out)
        pre_m = re.search(r'"preset"\s*:\s*"([^"]+)"', out)
 
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
     
    return {
        "ver": wrt_m.group(1) if wrt_m else None,
        "preset": pre_m.group(1) if pre_m else None,
    }

 
if __name__ == '__main__':
    get_serial_number()
    print(get_driver_versions())
    print(get_bios_version())
    print(get_platform_brand())
    print(get_platform_name())
    print(get_os_version())
    print(get_cpu_name())
    print(get_teams_version())
    print(get_connected_wifi_name())
    print(get_connected_wifi_band())
    print(get_wrt_version_and_preset())
 
 

