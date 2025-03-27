from utils import Utils
from utils import log as logger
import time
from bt_control import BluetoothControl as b_control
from wrt_controller import WRTController

Headset = "Dell WL5024 Headset"
S4_sleep_time_s = 60
Wake_up_time_s = 30


if __name__ == '__main__':
    total_test_times = 0
    pass_test_times = 0
    cmd = f'pwrtest.exe /sleep /s:4 /c:1 /d:{S4_sleep_time_s} /p:{Wake_up_time_s}'
    while True:
        #Use MSFT tool to make laptop go to s4 
        Utils.run_sync_cmd(cmd=cmd)
        #Check the headset connect status
        time.sleep(10)
        res = b_control.status_check(target=Headset, type="AudioEndpoint")
        if  res:
            logger.info('headset connect successfully')
            pass_test_times+=1
        else:
            logger.error('headset cannot connect DUT after s4!')
            logger.info('record wrt report...')
            WRTController.dump_wrt_log()
            logger.info('wrt report dump finish')
        total_test_times+=1
        logger.info(f'test pass {pass_test_times} times')
        logger.info(f'total test  {total_test_times} times')
        time.sleep(Wake_up_time_s)

    
            

