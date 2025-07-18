

from bt_control import BluetoothControl as b_control
from pynput.keyboard import Key, Controller
from teams_meeting_control import MeetingControl 
from teams_call.auto_vpt.vpt_contoller import VPTControl
from wrt_controller import WRTController
from audio_detect_control import AudioDetectController
from video_control import VideoControl
from utils import log  as logger
from utils import Utils
from enum import Enum
import serial.tools.list_ports
import time
import serial
import os
import pygame
import pyautogui
from datetime import datetime



class States(Enum):
    idle = 0
    go_to_s3 = 1
    go_to_s4 = 2

class Headset(Enum):
    idle = 0
    turn_on_off = 1

class SoundOuput(Enum):
    Teams = 1
    Local = 2
    Teams_Local = 3


headset = "Zone"
target_port_desc = "USB-SERIAL CH340"
teams_url = "https://teams.microsoft.com/l/meetup-join/19%3ameeting_MWQ5MTEwZmUtNWZkMy00YzZkLTgwOTMtNWVjMTc3NjMxZWMz%40thread.v2/0?context=%7b%22Tid%22%3a%228e44b933-0b1e-4e67-be0c-c7e0761eb4db%22%2c%22Oid%22%3a%2232692ba0-ede0-450b-8142-3f487cabff7b%22%7d"
Timeout_s = 5
sleep_time_s = 180
wake_up_time_s = 60
states = States.go_to_s4
output_source = SoundOuput.Local
headset_setting = Headset.idle
continue_fail_limit = 5


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



def arduino_board_check() -> str:
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
    
def headset_init(headset_states:Headset,ser:serial.Serial, command:bytes)->bool:
    '''
    headset states init and check
    idle: only check the headset states, don't turn on off the headset power
    turn_on_off: turn on the headset and then check the connect states
    '''
    counter = 0

    match headset_states:
        case Headset.turn_on_off:
            while counter < Timeout_s:
                if b_control.status_check(target=headset, type="AudioEndpoint"):
                    print("Headset connect!")
                    return True
                else:
                    print("headset doesn't connet, click the power button to turn on")
                    ser.write(command)
                    time.sleep(12)
                    counter+=1
            return False
        case Headset.idle:
            return b_control.status_check(target=headset, type="AudioEndpoint")

    

def headset_del(headset_states:Headset, ser:serial.Serial, command:bytes)->bool:
    '''
    idle: do nothing
    turn on off: turn off the headset and make sure the headset is disconnect
    '''
    match headset_states:
        case Headset.turn_on_off:
            counter = 0
            while counter <Timeout_s:
                if not b_control.status_check(target=headset, type="AudioEndpoint"):
                    print("Headset disconnect!")
                    return True
                else:
                    print("headset still, click the power button to turn off")
                    ser.write(command)
                    time.sleep(10)
                    counter+=1
            return False
        case Headset.idle:
            return True
        

def voice_detect(ser:serial.Serial, command:bytes)->bool:
    '''
    detect the sound
    '''
    ser.write(command)
    time.sleep(3)
    res = ser.read()
    print(f'*******************res = {res}***********************')
    return True if b'1' in res else False


def buzzer_buzzing(command:bytes)->bool:
    '''
    let buzzer start buzzing for 5 sec
    '''
    ser.write(command)

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


def get_arduino_port()->str:
    '''
    check and get the arduino board serial port
    '''
    serial_port = ""
    while True:
        serial_port = arduino_board_check()
        if serial_port=="":
            print("Please connect the arduino board! and press any key to continue")
            input()
        else:
            break
    
    return serial_port


def output_test_init(output_source:SoundOuput)->bool:
    '''
    doing some pre init before test the headset output function , like open teams or local music
    '''
    match output_source:
        case SoundOuput.Teams:
            # open the teams call and join the meeting 
            res = open_teams_call_and_join_meeting(t_control=t_control)
            if not res:
                logger.error('Can not join the Teams call meeting!')
                close_teams_call_and_vpt()
                return False
            print("Join the meeting...")
            # teams call robot join
            res = v_control.vpt_bot_join()
            if not res:
                logger.error('Can not execute VPT successfully')
                close_teams_call_and_vpt()
                return False
            print("VPT teams robot join the meeting...")

        case SoundOuput.Local:
            videoControl = VideoControl(path=os.path.join('\\','local_music','test.mp3'))
            videoControl.play()

        case SoundOuput.Teams_Local:

             # open the teams call and join the meeting 
            res = open_teams_call_and_join_meeting(t_control=t_control)
            if not res:
                logger.error('Can not join the Teams call meeting!')
                close_teams_call_and_vpt()
                return False
            print("Join the meeting...")
            # start playing local music after joining the teams call meeting
            videoControl = VideoControl(path=os.path.join('\\','local_music','test.mp3'))
            videoControl.play()



    return True
        


def output_test_del(output_source:SoundOuput)->bool:
    '''
    doing some del before test the headset output function , like close teams or local music
    '''
    match output_source:

        case SoundOuput.Teams:
            #close the teams call and vpt robot
            close_teams_call_and_vpt()
            print("Close the meeting and VPT robot")
          
        case SoundOuput.Local:
            #close the media player
            VideoControl.stop_play()

        case SoundOuput.Teams_Local:
            MeetingControl.close_teams()
            VideoControl.stop_play()
            #close the teams call and vpt robot
    return True

def mouse_function_detect(ser:serial.Serial, command:bytes)->bool:
    """_summary_
        check mouse function still working or not
    Returns:
        bool: _description_
    """
    counter = 0
    pygame.init()
    screen = pygame.display.set_mode((2560, 1600))
    running = True
    logger.info("BLE mouse function test start")
    #control mouse clicking
    ser.write(command)
    #start cehcking mouse click
    while counter < Timeout_s:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.error("mouse function test have unexpected issue!")
                pygame.quit()
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                print("BLE mouse function pass!")
                pygame.quit()
                return True
        counter+=1
        time.sleep(1)
    pygame.quit()
    logger.error("mouse function test fail!")
    return False

def mouse_function_detect_s3(ser:serial.Serial, command:bytes, sleep_time:int)->bool:
    """_summary_
        check mouse function still working or not (s3 states)
    Returns:
        bool: _description_
    """
    print("BLE mouse function test setting...")
    #control mouse clicking
    #command.join(sleep_time)
    ser.write(command)
    print(f"BLE mouse will click after {sleep_time} second! ")
    return True

def arduino_serial_port_reset(ser:serial.Serial):
    """_summary_
    reset the arduino serial port after s3 or s4
    Args:
        ser (serial.Serial): _description_

    Returns:
        _type_: _description_
    """
    ser.close()
    time.sleep(5)
    return serial.Serial(serial_port, 115200)

def dut_states_init(states:States)->None:
    """_summary_
    setting dut states, s3 ,s4 or idle 

    Args:
        states (States): _description_
    """
    match states:

        case States.idle:
            pass
        
        case States.go_to_s3:
            mouse_function_detect_s3(ser=ser,command=cmd_mouse_delay_clicking,sleep_time=sleep_time_s)
            go_to_sleep()
            
        
        case States.go_to_s4:
            #go to sleep mode first and waiting for mouse click
            cmd_pwrtest = f'pwrtest\pwrtest.exe /sleep /s:4 /c:1 /d:{sleep_time_s} /p:{wake_up_time_s}'
            print(f'Go to s{states} mode!')
            Utils.run_sync_cmd(cmd=cmd_pwrtest)
            

    
if __name__ == "__main__":
    serial_port = get_arduino_port()
    cmd_servo = str.encode("0")
    cmd_voice_detect = str.encode("1")
    cmd_buzzer = str.encode("2")
    cmd_mouse_clicking = str.encode("3")
    cmd_mouse_delay_clicking = str.encode("4")
    ser = serial.Serial(serial_port, 115200)
    t_control = MeetingControl(meeting_link=teams_url,teams_path="\\teams_call\\")
    v_control = VPTControl()
    time.sleep(5)
    test_retry_times = 3
    test_success_count = 0
    test_total_count = 0
    continue_fail_count = 0
    keyboard = Controller()
    issue_occuring_time = ""

    while(True):

        res_mouse = False
        res_output = False
        output_init_flag = 0
        res_input = True
        logger.info('Test start...')

        #dut states setting 

        dut_states_init(states=states)

        time.sleep(wake_up_time_s)

        # reset the serport states
        ser = arduino_serial_port_reset(ser=ser)
        time.sleep(5)
        
        # mouse function test
        res_mouse = mouse_function_detect(ser = ser, command= cmd_mouse_clicking)
        time.sleep(10)

        # headset init
        if not headset_init(headset_setting, ser = ser, command= cmd_servo):
            logger.error('Can not turn on the Headset or headset can not connect to the dut, stop testing!')
            WRTController.dump_wrt_log()
            break
        print("Turn on the headset successfully, connected")
        time.sleep(10)

        logger.info('Start headset input function test...')
        #headset input function test
        test_time = 0
        while not res_input:
            ad_Controller = AudioDetectController(headset= headset, threshold=150)
            buzzer_buzzing(command=cmd_buzzer)
            res_input = ad_Controller.audio_detect()
            if test_time > test_retry_times:
                if continue_fail_count == 0 :
                        issue_occuring_time = datetime.now()
                logger.error('***Headset input function have some issue!***')
                WRTController.dump_wrt_log()
                break
            test_time+=1
        print("Headset input function test finish")
        

        time.sleep(5)
        logger.info('Start headset output function test...')
        test_time = 0
        while not res_output:
            # doing output test init and headset output function check
            if output_test_init(output_source=output_source):
                # play sound 20 sec before detect
                time.sleep(20)
                #voice detect
                res_output = voice_detect(ser = ser, command=cmd_voice_detect)
                output_test_del(output_source=output_source)
            else:
                output_test_del(output_source=output_source)
                logger.error('***Headset output test init have some issue!***')
                output_init_flag = 1
            if test_time>test_retry_times:
                    if continue_fail_count == 0 :
                        issue_occuring_time = datetime.now()
                    logger.error('***Headset output function have some issue!***')
                    WRTController.dump_wrt_log()
                    break
            test_time+=1

        print("Headset output function test finish")

        #turn off the headset
        if not headset_del(headset_setting, ser = ser, command= cmd_servo):
            logger.error('Can not turn off the Headset, stop test!')
            break
        print("Headset turn off successfully, disconneted")

        #summary the test result
        logger.info(f'mouse function: {res_mouse}')
        logger.info(f'headset output function: {res_output}, init issue:{output_init_flag}')
        logger.info(f'headset input function: {res_input}')
        if res_output and res_input:
            test_success_count+=1
            continue_fail_count = 0
        else:
            continue_fail_count+=1
        test_total_count+=1
        logger.info(f'successfully test  {test_success_count} times')
        logger.info(f'Total test  {test_total_count} times')
        if continue_fail_count >= continue_fail_limit:
            logger.info("out of maxium continue fail range, stop testing!")
            logger.info(f"first issue occuring time: {issue_occuring_time}")
            break
    
    print('press any key to leave')
    input()






       
    
    
        



    
    
    


            
    
    

        

