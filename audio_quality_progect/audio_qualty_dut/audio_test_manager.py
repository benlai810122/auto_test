
import os
from mic_recording_manager import MicRecorder as MR
import grpc 
import audio_test_pb2 as pb2
import audio_test_pb2_grpc as pb2_grpc
from teams_meeting_manager import MeetingControl as TC

TEAMS_CALL_LINK = "https://teams.microsoft.com/l/meetup-join/19%3ameeting_Njg2YTEwNDUtNTFlMy00ZDYyLWJjZDAtZDkwNGEzZjYxYjY1%40thread.v2/0?context=%7b%22Tid%22%3a%224d5ee319-c659-429d-bc2f-71fd32fb7d9f%22%2c%22Oid%22%3a%22434e345a-de7c-46e5-ac98-bcc931a80aaa%22%7d"

class AudioTestManager:
    def __init__(self):
        self._active = {}  # key: (run_id, mode) -> out_path
        self.mr = MR()
        self.tc = TC(TEAMS_CALL_LINK,'teams_call')

    def prepare(self, run_id: str, mode: int, device_id: str, sr: int, ch: int) -> bool:
        #Start teams call meeting
        if not self.tc.open_teams_and_join_meeting():
            return False 
        # Validate devices, reserve paths, etc.
        os.makedirs(self._run_dir(run_id), exist_ok=True)
        return True

    def start(self, run_id: str, mode: int) -> str:
        #start recording and save the output path
        out_path = os.path.join(self._run_dir(run_id), "mic.wav" if mode == pb2.MIC else "loopback.wav")
        self.mr.start(out_path=out_path) 
        self._active[(run_id, mode)] = out_path
        return out_path

    def stop(self, run_id: str, mode: int) -> str:
        # Stop recording 
        out_path = self._active.get((run_id, mode))
        if not out_path:
            raise RuntimeError("Recording not active")
        self.mr.stop() 
        return out_path

    def _run_dir(self, run_id: str) -> str:
        current_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_path,'record', run_id)
