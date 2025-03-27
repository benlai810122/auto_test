

from pynput.keyboard import Key, Controller
import time
import serial
import logging
import os

# Python Log
PYTHON_LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")

# Log formatter
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# setting log function
def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file, mode="w")
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


logger = setup_logger("server_message", PYTHON_LOG_FILE)


def go_to_sleep():
    # Maximize teams  window
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

def send_cmd_and_waiting_for_response(ser:serial.Serial, command:bytes, target_port:str)->serial.Serial:
    if ser == None:
        ser = serial.Serial(target_port, 115200)
    else:
        ser.close()
        time.sleep(5)
        ser = serial.Serial(target_port, 115200)
    time.sleep(5)
    ser.write(command)
    time.sleep(5)
    print("waiting for the message...")
    ser.read(1)
    return ser
    
   
        
if __name__ == '__main__':
    target_port_desc = "USB-SERIAL CH340"
    target_port = None
    mode = 0
    ser = None
    ms_sleep = [180,360,1800]
    os_wakeup = 120
    click_freg = 5
    delay = 0.2
    click_times = int(os_wakeup/click_freg)

    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in ports:
        if target_port_desc in desc:
            target_port = port
            print(f"{port}: {desc}")
    if not target_port:
        print("can't not find target port!")
        exit()
   
    print('Enter your mode:')
    print('(0 = mouse click randomly)')
    print('(1 = ms:3min os:2min)')
    print('(2 = ms:6min os:2min)')
    print('(3 = ms:30min os:2min)')
    while(True):
        mode = input()
        if mode != '0' and mode != '1' and mode != '2' and mode != '3':
            print("wrong mode, please input again!")
        else:
            break
    command = str.encode(mode)
   
    if mode == '0':
        ser = serial.Serial(target_port, 115200)
        time.sleep(5)
        ser.write(command)
        time.sleep(3)
        click_times = 0
        while (True):
            ser.read()
            print("mouse click!")
            click_times+=1
            logger.info(f"mouse click {click_times} times!")



    else:
        round_count = 0
        while(True):
            try:
                ser = send_cmd_and_waiting_for_response(ser=ser,command=command,target_port=target_port)
            except:
                print("serial port connect fail, close and reconnect again!")
                ser = send_cmd_and_waiting_for_response(ser=ser,command=command,target_port=target_port)
                
            print("os go to sleep!")
            go_to_sleep()
            time.sleep(10)
            round_count+=1
            print(f"{round_count} round!")
            logger.info(f"{round_count} round!")
