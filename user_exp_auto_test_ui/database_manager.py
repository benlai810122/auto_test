
from dataclasses import dataclass, asdict
import yaml
import requests


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

BASE_URL = "http://192.168.0.145:8001"

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
    response = requests.post(f"{BASE_URL}/reports", json=payload) 
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200
    return response.json()["id"]