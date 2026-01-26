import threading
import queue
import time
import numpy as np
import sounddevice as sd
import soundfile as sf

class MicRecorder:
    def __init__(self):
        self._q = queue.Queue()
        self._stop = threading.Event()
        self._thread = None
        self._stream = None
        self._out_path = None

    def start(self, out_path: str, device_index: int | None = None,
              samplerate: int = 48000, channels: int = 1, blocksize: int = 4800):
        """
        device_index: from sd.query_devices(); None = default input
        blocksize: frames per callback (~0.1s at 48kHz)
        """ 
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Already recording")

        self._stop.clear()
        self._out_path = out_path

        def callback(indata, frames, time_info, status):
            if status:
                # You can log status for debugging xruns, overflows, etc.
                pass
            # Copy because indata is reused by PortAudio
            self._q.put(indata.copy())

        def writer():
            with sf.SoundFile(out_path, mode="w",
                            samplerate=samplerate,
                            channels=channels,
                            subtype="PCM_16") as wav:
                while not self._stop.is_set() or not self._q.empty():
                    try:
                        data = self._q.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    # ensure shape [frames, channels]
                    if data.ndim == 1:
                        data = data[:, None]
                    if data.shape[1] != channels:
                        data = data[:, :channels] if data.shape[1] > channels else np.tile(data, (1, channels))
                    wav.write(data)

        # Start stream + writer thread
        self._thread = threading.Thread(target=writer, daemon=True)
        self._thread.start()

        self._stream = sd.InputStream(
            device=device_index,
            channels=channels,
            samplerate=samplerate,
            blocksize=blocksize,
            dtype="float32",
            callback=callback,
        )
        self._stream.start()
        

    def stop(self, timeout: float = 5.0):
        self._stop.set()
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._thread:
            self._thread.join(timeout=timeout)
        return self._out_path

# --- Example usage ---
if __name__ == "__main__":
    rec = MicRecorder()
    rec.start(r"C:\Users\Admin\Desktop\auto_workspace\auto_test\audio_quality_progect\tx_mic.wav", device_index=None, samplerate=48000, channels=1)
    time.sleep(10)
    print("Saved:", rec.stop())
