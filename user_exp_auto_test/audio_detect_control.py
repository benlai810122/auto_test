import pyaudio
import numpy as np
import time


class AudioDetectController:
    '''
    audio detecter
    '''

    __headset_name = ''
    __chunk_size = 1024  # Size of each audio chunk
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
  

    def audio_detect(self)->bool:
        res = False
        audio = pyaudio.PyAudio()
        dev_index = self.__device_checking(audio=audio)
        print(dev_index)
        if dev_index < 0:
            return False

        stream =  audio.open(format=self.__sample_format,
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
        audio.terminate()

        return res
        

    def __device_checking(self,audio:pyaudio.PyAudio)->int:
        info = audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                dev_name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
                if self.__headset_name in dev_name:
                    return i
        return -1


if __name__ == '__main__':
    Headset = "Dell WL5024 Headset"
    ad_Controller = AudioDetectController(headset= Headset, threshold=500)
    if ad_Controller.audio_detect():
        print('sound detected!')
    else:
        print('sound not detected!')