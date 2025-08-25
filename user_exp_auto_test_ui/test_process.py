

from dataclasses import dataclass, asdict
from bt_control import BluetoothControl as b_control
from pynput.keyboard import Key, Controller
from teams_meeting_control import MeetingControl 
from teams_call.auto_vpt.vpt_contoller import VPTControl
from wrt_controller import WRTController
from audio_detect_control import AudioDetectController
from video_control import VideoControl
from utils import Utils
from enum import Enum
import serial.tools.list_ports 
from serial.serialutil import SerialException
import time
import serial
import os
import pygame
import pyautogui
from datetime import datetime
import yaml
from utils import log  as logger
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


class Power_States(Enum):
    idle = 0
    go_to_s3 = 1
    go_to_s4 = 2

class Headset(Enum):
    idle = 0
    turn_on_off = 1

class SoundOuput(Enum):
    Teams = 0
    Local = 1
    Teams_Local = 2

#Arduino cmd setting
CMD_servo = str.encode("0")
CMD_voice_detect = str.encode("1")
CMD_buzzer = str.encode("2")
CMD_mouse_clicking = str.encode("3")
CMD_mouse_delay_clicking = str.encode("4")
CMD_mouse_random_clicking = str.encode("5")
CMD_keyboard_clicking = str.encode("6")
g_COM_PORT = ""


@dataclass
class Basic_Config:
    headset:str = "Zone"
    target_port_desc:str = "USB-SERIAL CH340"
    teams_url:str = "https://teams.microsoft.com/l/meetup-join/19%3ameeting_MWQ5MTEwZmUtNWZkMy00YzZkLTgwOTMtNWVjMTc3NjMxZWMz%40thread.v2/0?context=%7b%22Tid%22%3a%228e44b933-0b1e-4e67-be0c-c7e0761eb4db%22%2c%22Oid%22%3a%2232692ba0-ede0-450b-8142-3f487cabff7b%22%7d"
    timeout_s:int = 5
    sleep_time_s:int = 30
    wake_up_time_s:int = 60
    output_source:int = SoundOuput.Local.value
    headset_setting:int = Headset.idle.value
    test_retry_times:int = 3
    continue_fail_limit:int = 5
    output_source_play_time_s:int = 20
    task_schedule:str = "MS,Idle,headset_output"
    test_times:int = 100
    com:str = ""
    



def load_basic_config(file_path:str)->Basic_Config:
    with open(file_path) as f:
        data = yaml.safe_load(f)
    return Basic_Config(**data)

def save_report(config: Basic_Config, total_cycles: int, fail_times: int, error_message=""):
    wb = Workbook()
    ws = wb.active
    ws.title = "BT Test Report"

    # Title
    ws.merge_cells("A1:D1")
    title_cell = ws["A1"]
    title_cell.value = "Bluetooth Device Test Report"
    title_cell.font = Font(size=16, bold=True)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Config Section
    ws.append([])
    ws.append(["Configuration Settings"])
    ws["A3"].font = Font(size=14, bold=True)

    row_start = ws.max_row + 1
    for key, value in asdict(config).items():
        if isinstance(value, Enum):
            value = value.name
        ws.append([key, str(value)])

    # Summary Section
    ws.append([])
    ws.append(["Test Summary"])
    ws["A{}".format(ws.max_row)].font = Font(size=14, bold=True)

    ws.append(["Total Test Cycles", total_cycles])
    ws.append(["Pass Times", (total_cycles-fail_times)])
    ws.append(["Fail Times", fail_times])
    ws.append(["Error Message", error_message])

    # Make it look cleaner
    for col in ["A", "B"]:
        ws.column_dimensions[col].width = 25

    current_time = datetime.now()
    timestamp_str = current_time.strftime("%Y%m%d_%H%M%S")
    filename = f"report\\test_report_{timestamp_str}.xlsx"

    wb.save(filename)
    print(f"✅ Report saved as {filename}")



def go_to_sleep():
    '''
    using keybaord to go to sleep mode
    '''
    keyboard = Controller()
    keyboard.press(Key.cmd)
    time.sleep(0.3)
    keyboard.press('x')
    time.sleep(0.3)
    keyboard.release('x')
    time.sleep(0.3)
    keyboard.release(Key.cmd)
    time.sleep(0.3)
    keyboard.tap('u')
    time.sleep(0.3)
    keyboard.tap('s')



def arduino_board_check(target_port_desc:str) -> str:
    '''
    arduino board checking
    '''
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in ports:
        if target_port_desc in desc:
            target_port = port
            print(f"{port}: {desc}")
            return port
    if not target_port:
        return ""
    
def headset_init(headset_states:Headset,ser:serial.Serial, command:bytes,headset:str,timeout_s:int)->bool:
    '''
    headset states init and check
    idle: only check the headset states, don't turn on off the headset power
    turn_on_off: turn on the headset and then check the connect states
    '''
    counter = 0

    match headset_states:
        case Headset.turn_on_off.value:
            while counter < timeout_s:
                if b_control.status_check(target=headset, type="AudioEndpoint"):
                    print("Headset connect!")
                    return True
                else:
                    print("headset doesn't connet, click the power button to turn on")
                    ser.write(command+b'\n')
                    time.sleep(12)
                    counter+=1
            return False
        case Headset.idle.value:
            return b_control.status_check(target=headset, type="AudioEndpoint")

    

def headset_del(headset_states:Headset, ser:serial.Serial, command:bytes,headset:str, timeout_s:int)->bool:
    '''
    idle: do nothing
    turn on off: turn off the headset and make sure the headset is disconnect
    '''
    match headset_states:
        case Headset.turn_on_off.value:
            counter = 0
            while counter < timeout_s:
                if not b_control.status_check(target=headset, type="AudioEndpoint"):
                    print("Headset disconnect!")
                    return True
                else:
                    print("headset still, click the power button to turn off")
                    ser.write(command+b'\n')
                    time.sleep(10)
                    counter+=1
            return False
        case Headset.idle.value:
            return True
        

def voice_detect(ser:serial.Serial, command:bytes)->bool:
    '''
    detect the sound
    '''
    ser.write(command+b'\n')
    time.sleep(3)
    res = ser.read()
    print(f'*******************res = {res}***********************')
    return True if b'1' in res else False


def buzzer_buzzing(ser:serial.Serial,command:bytes)->bool:
    '''
    let buzzer start buzzing for 5 sec
    '''
    ser.write(command+b'\n')

def open_teams_call_and_join_meeting( t_control:MeetingControl)->bool:
    '''
    open teams call and join the specific meeting
    '''
    t_control.open_teams()
    time.sleep(10)
    if t_control.join_meeting():
        time.sleep(5)
        #t_control.open_camera_and_mute()
        return True
    else:
        return False
    

def close_teams_call_and_vpt():
    '''
    close the teams call and vpt robot
    '''
    MeetingControl.end_meeting()
    time.sleep(5)
    MeetingControl.close_teams()
    VPTControl.vpt_bot_close()


def get_arduino_port(port:str, log_callback)->str:
    '''
    check and get the arduino board serial port
    '''
    serial_port = ""
    try:
        serial_port = arduino_board_check(target_port_desc=port)
        log_callback(f"serial port detected: {serial_port}")
    except Exception as e:
        log_callback("please insert the arduino board!")

    return serial_port


def output_test_init(output_source:SoundOuput,t_control:MeetingControl,v_control:VPTControl,log_callback)->bool:
    '''
    doing some pre init before test the headset output function , like open teams or local music
    '''
    match output_source:
        case SoundOuput.Teams.value:
            # open the teams call and join the meeting 
            res = open_teams_call_and_join_meeting(t_control=t_control)
            if not res:
                log_callback('Can not join the Teams call meeting!')
                close_teams_call_and_vpt()
                return False
            print("Join the meeting...")
            # teams call robot join
            res = v_control.vpt_bot_join()
            if not res:
                log_callback('Can not execute VPT successfully')
                close_teams_call_and_vpt()
                return False
            print("VPT teams robot join the meeting...")

        case SoundOuput.Local.value:
            videoControl = VideoControl(path=os.path.join('\\','local_music','test.mp3'))
            videoControl.play()

        case SoundOuput.Teams_Local.value:

             # open the teams call and join the meeting 
            res = open_teams_call_and_join_meeting(t_control=t_control)
            if not res:
                log_callback('Can not join the Teams call meeting!')
                close_teams_call_and_vpt()
                return False
            print("Join the meeting...")
            # start playing local music after joining the teams call meeting
            videoControl = VideoControl(path=os.path.join('\\','local_music','test.mp3'))
            videoControl.play()
    return True


def headset_output_test(b_config:Basic_Config,ser:serial.Serial,log_callback,mouse_function_detect=None):
    log_callback('Start headset output function test...')
    test_time = 0
    t_control = MeetingControl(meeting_link=b_config.teams_url,teams_path="\\teams_call\\")
    v_control = VPTControl()
    res_mouse = True
    res_output = False
    while not res_output:
        # doing output test init and headset output function check
        if output_test_init(output_source=b_config.output_source,t_control=t_control
                            ,v_control=v_control,log_callback=log_callback):
            #start play sound before detect
            time.sleep(b_config.output_source_play_time_s)

            if mouse_function_detect:
                res_mouse = mouse_function_detect(ser,CMD_mouse_clicking ,5,log_callback)
                if not res_mouse:
                    log_callback('Mouse function have some issue when audio playing!')
                    log_callback('Dump WRT log...')
                    WRTController.dump_wrt_log()

            #voice detect
            res_output = voice_detect(ser = ser, command=CMD_voice_detect)
            output_test_del(output_source=b_config.output_source)
            if not res_output:
                log_callback('headset output test fail, retry again!')

        else:
            output_test_del(output_source=b_config.output_source)
            log_callback('***Headset output test init have some issue!***')
        if test_time>b_config.test_retry_times:
            log_callback('***Headset output function have some issue!***')
            log_callback('Dump WRT log...')
            WRTController.dump_wrt_log()
            return False
        test_time+=1
    log_callback("Headset output function test finish")
    return res_mouse and res_output
    
        
def output_test_del(output_source:SoundOuput)->bool:
    '''
    doing some del before test the headset output function , like close teams or local music
    '''
    match output_source:

        case SoundOuput.Teams.value:
            #close the teams call and vpt robot
            close_teams_call_and_vpt()
            print("Close the meeting and VPT robot")
          
        case SoundOuput.Local.value:
            #close the media player
            VideoControl.stop_play()

        case SoundOuput.Teams_Local.value:
            MeetingControl.close_teams()
            VideoControl.stop_play()
            #close the teams call and vpt robot
    return True

def mouse_function_detect(ser:serial.Serial, command:bytes, timeout_s:int,log_callback)->bool:
    """_summary_
        check mouse function still working or not
    Returns:
        bool: _description_
    """
    counter = 0
    pygame.init()
    screen = pygame.display.set_mode((2560, 1600))
    running = True
    log_callback("BLE mouse function test start")
    #control mouse clicking
    ser.write(command+b'\n')
    #start cehcking mouse click
    while counter < timeout_s:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                log_callback("mouse function test have unexpected issue!")
                pygame.quit()
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                log_callback("BLE mouse function pass!")
                pygame.quit()
                return True
        counter+=1
        time.sleep(1)
    pygame.quit()
    return False

def mouse_random_click(ser:serial.Serial, command:bytes, timeout_s:int,log_callback)->bool:
    log_callback("mouse random click start!")
    #control mouse randomly clicking
    ser.write(command+b'\n')
    #waiting for the mouse click end
    ser.read()
    log_callback("mouse random click finish!")
    return True


def mouse_function_detect_s3(ser:serial.Serial, command:bytes, sleep_time:int)->bool:
    """_summary_
        check mouse function still working or not (s3 states)
    Returns:
        bool: _description_
    """
    print("BLE mouse function test setting...")
    cmd = f'4,{sleep_time}\n'.encode()
    ser.write(cmd)
    print(f"BLE mouse will click after {sleep_time} second! ")
    return True

def arduino_serial_port_reset(ser:serial.Serial,serial_port:str):
    """_summary_
    reset the arduino serial port after s3 or s4
    Args:
        ser (serial.Serial): _description_

    Returns:
        _type_: _description_
    """
    try:
        ser.close()
    except:
        pass
    time.sleep(5)
    return serial.Serial(serial_port, 115200)

def wait_for_port(port_name, timeout=30):
    """Wait until a specific COM port reappears"""
    start = time.time()
    while time.time() - start < timeout:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        print(ports)
        if port_name in ports:
            return True
        time.sleep(1)
    return False

def dut_states_init(power_states:Power_States,wake_up_time_s:int,sleep_time_s:int,ser:serial.Serial)->None:
    """_summary_
    setting dut states, s3 ,s4 or idle 

    Args:
        states (States): _description_
    """
    match power_states:
        case Power_States.idle:
            time.sleep(wake_up_time_s)
        case Power_States.go_to_s3:
            mouse_function_detect_s3(ser=ser,command=CMD_mouse_delay_clicking,sleep_time=sleep_time_s)
            go_to_sleep()
        case Power_States.go_to_s4:
            #go to sleep mode first and waiting for mouse click
            cmd_pwrtest = f'pwrtest\pwrtest.exe /sleep /s:4 /c:1 /d:{sleep_time_s} /p:{wake_up_time_s}'
            Utils.run_sync_cmd(cmd=cmd_pwrtest)


def safe_write(ser:serial.Serial, data, baudrate=115200):
    global g_COM_PORT
    #safe serial wirte cmd to aviod issue
    try:
        ser.write(data)
    except SerialException as e:
        print(f"[WARN] Serial exception: {e}")
        try:
            ser.close()
        except:
            pass
        
        time.sleep(1)  # wait a bit for device to re-enumerate
        ser = serial.Serial(g_COM_PORT, baudrate, timeout=30)
        ser.write(data)
        ser.close()
    


def run_test(test_case:str, b_config:Basic_Config, log_callback)->bool:
    """_summary_

    Args:
        test_case (str): test case
        b_config (Basic_Config): the configation of the test
        log_callback (_type_): present the log one textbox and save the log txt

    Returns:
        bool: _description_
    """
    #connect to arduino board
    global g_COM_PORT
    res = True
    g_COM_PORT = b_config.com
    ser:serial.Serial = None

    #do nothing if test_case = Idle
    if test_case == 'Idle':
        log_callback(f"waiting for {b_config.wake_up_time_s} sec...")
        time.sleep(b_config.wake_up_time_s)
        return True


    if not g_COM_PORT:
        log_callback('Can not find the arduino board!')
        return False
    
    try:
        if wait_for_port(g_COM_PORT,30):
            ser = serial.Serial(g_COM_PORT, 115200, timeout=30)
            time.sleep(5)
        else:
            log_callback(f'Cant not find the serial device')
            return False
        
    except Exception as ex:
        log_callback(f'Serial port connection error:{ex}')
        return False

    log_callback(f'test case: {test_case}')

    match test_case:
        
        #case 'Idle' :
            #log_callback(f"waiting for {b_config.wake_up_time_s} sec...")
            #dut_states_init(power_states=Power_States.idle, wake_up_time_s=b_config.wake_up_time_s,
                    #sleep_time_s=b_config.sleep_time_s,ser=ser)
        
        case 'MS':
            log_callback(f"go to MS states for {b_config.sleep_time_s} sec...")
            dut_states_init(power_states=Power_States.go_to_s3, wake_up_time_s=b_config.wake_up_time_s,
                    sleep_time_s=b_config.sleep_time_s,ser=ser)
            #make sure the laptop go to MS states
            time.sleep(5)
            
        case 'S4':
            log_callback(f"go to s4 states for {b_config.sleep_time_s} sec...")
            dut_states_init(power_states=Power_States.go_to_s4, wake_up_time_s=b_config.wake_up_time_s,
                    sleep_time_s=b_config.sleep_time_s,ser=ser)
            
            
        case 'Mouse_function':
            # mouse function test
            res = mouse_function_detect(ser = ser, command= CMD_mouse_clicking,
                                               timeout_s=b_config.timeout_s,log_callback=log_callback)
            if not res:
                log_callback('mouse function test fail!')
                log_callback('dump wrt log...')
                WRTController.dump_wrt_log()

            time.sleep(5)
            
        case 'Mouse_random':
            # mouse function test
            res = mouse_random_click(ser = ser, command= CMD_mouse_random_clicking,
                                               timeout_s=b_config.timeout_s,log_callback=log_callback)
            if not res:
                log_callback('mouse function test fail!')
                log_callback('dump wrt log...')
                WRTController.dump_wrt_log()

            time.sleep(5)
           
        case 'Mouse_function + Headset output':
            # mouse function test
            res = headset_output_test(b_config=b_config,ser=ser,log_callback=log_callback,mouse_function_detect=mouse_random_click)
            time.sleep(5)
        
        
        case 'Headset_init':
            # headset init
            res = headset_init(headset= b_config.headset, headset_states=b_config.headset_setting,
                                 timeout_s= b_config.timeout_s, ser = ser, command= CMD_servo)
            if not res:
                log_callback('Can not turn on the Headset or headset can not connect to the dut, stop testing!')
                log_callback('dump wrt log...')
                WRTController.dump_wrt_log()
            else:
                log_callback("Turn on the headset successfully, connected")
            time.sleep(5)

        case 'Headset_input':
            log_callback('Start headset input function test...')
            #headset input function test
            test_time = 0
            while not res:
                ad_Controller = AudioDetectController(headset= b_config.headset, threshold=150)
                buzzer_buzzing(ser=ser,command=CMD_buzzer)
                res = ad_Controller.audio_detect()
                if test_time > b_config.test_retry_times:
                    log_callback('***Headset input function have some issue!***')
                    WRTController.dump_wrt_log()
                    break
                test_time+=1
            log_callback("Headset input function test finish")
            time.sleep(5)
        
    
        case 'Headset_output':
            res = headset_output_test(b_config=b_config,ser=ser,log_callback=log_callback)

        case 'Headset_del':
            res = headset_del(headset = b_config.headset,headset_states=b_config.headset_setting,
                               timeout_s=b_config.timeout_s, ser = ser, command= CMD_servo)
            if not res:
                log_callback('Can not turn off the Headset, stop test!')
            else:
                log_callback("Headset turn off successfully, disconneted")
        
        case _:
            log_callback("Not match any test case, please check!")
            res = False
        
    
    #close serial connect after testing:
    try:
        print("Relsease serial port!")
        ser.close()
    except:
        pass

    return res


    #summary the test result
    '''
    if b_config.do_mouse_flag: log_callback(f'mouse function: {res_mouse}')
    if b_config.do_headset_output_flag: log_callback(f'headset output function: {res_output}, init issue:{output_init_flag}')
    if b_config.do_headset_input_flag: log_callback(f'headset input function: {res_input}')
    if (res_output or not b_config.do_headset_output_flag) and (res_input or not b_config.do_headset_input_flag) and (res_mouse or not b_config.do_mouse_flag) :
        test_success_count+=1
        continue_fail_count = 0
    else:
        continue_fail_count+=1
    test_total_count+=1
    log_callback(f'successfully test  {test_success_count} times')
    log_callback(f'Total test  {test_total_count} times')
    if continue_fail_count >= b_config.continue_fail_limit:
        log_callback("out of maxium continue fail range, stop testing!")
        log_callback(f"first issue occuring time: {issue_occuring_time}")
        break
     '''

    
if __name__ == "__main__":
    b_config  = Basic_Config()
    def log_callback(meg:str):
        print(meg)
        logger.info(meg)
    test_case = 'MS'
    run_test(test_case,b_config,log_callback=log_callback)





       
    
    
        



    
    
    


            
    
    

        

