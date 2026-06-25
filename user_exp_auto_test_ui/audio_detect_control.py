import pyaudio
import numpy as np
import time
from utils import log as logger

class AudioDetectController:
    '''
    audio detecter
    '''

    __headset_name = ''
    __chunk_size = 4096  # Size of each audio chunk
    __sample_format = pyaudio.paInt16  # Format of the audio samples
    __channels = 1  # Number of channels (1 for mono, 2 for stereo)
    __fs = 44100  # Sample rate (samples per second)
    __threshold = 200
    __timeout = 5

    def __init__(self, headset:str,chunk_size:int = 1024,threshold:int=300,timeout:int = 5):
        """
        init and set the local video path
        """
        self.__headset_name = headset
        self.__chunk_size = chunk_size
        self.__threshold = threshold
        self.__timeout = timeout
        self.__audio = pyaudio.PyAudio()
  

    def audio_detect(self)->bool:
        res = False
        stream = None
        dev_index = self.device_checking()
        print(dev_index)
        if dev_index < 0:
            return False
        
        try:
            stream =  self.__audio.open(format=self.__sample_format,
                        channels=self.__channels,
                        rate=self.__fs,
                        input=True,
                        frames_per_buffer=self.__chunk_size,
                        input_device_index = dev_index
                        )
            time_counter = 0
            while time_counter<self.__timeout :
                data = stream.read(self.__chunk_size,exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                max_audio_val = np.max(np.abs(audio_data))
                print(max_audio_val)
                if max_audio_val >= self.__threshold and max_audio_val < 0x7fff:
                    res = True
                    break
                time.sleep(0.01)
                time_counter+=0.01
            stream.stop_stream()
            stream.close()
            self.__audio.terminate()
        except OSError as os_error:
            if stream and stream.is_active:
                stream.stop_stream()
                stream.close()
            self.__audio.terminate()
            logger.error(f'Have unexpect error when test output function:{os_error}')
            return True #ignore the os_error
        return res


    def device_checking(self)->int:
        info = self.__audio.get_host_api_info_by_index(1)
        numdevices = info.get('deviceCount')
        input_index = -1
        output_found = False
        for i in range(0, numdevices):
            dev_info = self.__audio.get_device_info_by_host_api_device_index(1, i)
            dev_name = dev_info.get('name', '')
            if self.__headset_name not in dev_name:
                continue
            default_sample_rate = dev_info.get('defaultSampleRate', 0)
            if default_sample_rate <= 0:
                logger.error(f'Device "{dev_name}" has invalid sample rate: {default_sample_rate}')
                continue
            if dev_info.get('hostApi') is None:
                logger.error(f'Device "{dev_name}" has no valid host API')
                continue
            # Check input (mic) endpoint
            if dev_info.get('maxInputChannels') > 0 and input_index < 0:
                input_index = dev_info.get('index')
                print(f'Mic endpoint "{dev_name}" found, index={input_index}, '
                      f'sampleRate={default_sample_rate}, inputChannels={dev_info.get("maxInputChannels")}')
            # Check output (audio) endpoint
            if dev_info.get('maxOutputChannels') > 0:
                output_found = True
                logger.info(f'Audio endpoint "{dev_name}" found, index={dev_info.get("index")}, '
                      f'sampleRate={default_sample_rate}, outputChannels={dev_info.get("maxOutputChannels")}')

        if input_index < 0:
            logger.error(f'Headset "{self.__headset_name}" mic endpoint not found')
            return -1
        if not output_found:
            logger.error(f'Headset "{self.__headset_name}" audio output endpoint not found')
            return -1
        return input_index
    
    def audio_dect_terminate(self):
        if self.__audio :
            self.__audio.terminate()
 
     
if __name__ == '__main__':
    headset = "LE-Logitech Zone Wireless 2"
    ad_Controller = AudioDetectController(headset= headset, threshold=500)
    print(ad_Controller.device_checking())
     
    #else:
        #print('device dont exist')
    #if ad_Controller.audio_detect():
        #print('sound detected!')
    #else:
        #print('sound not detected!')