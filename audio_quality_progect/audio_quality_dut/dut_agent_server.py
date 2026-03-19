import os
from pathlib import Path
import time
import socket
from concurrent import futures
import grpc 
import audio_test_pb2 as pb2
import audio_test_pb2_grpc as pb2_grpc
from mic_recording_manager import MicRecorder as MR
from typing import Optional 
from audio_test_manager import AudioTestManager as ATM
from teams_meeting_manager import MeetingControl as TC
import webbrowser
import headset_status_check as hsc
from google.protobuf import empty_pb2
from utils import Utils
 
 

class DutAgent(pb2_grpc.DutAgentServicer):

    def __init__(self, rec_mgr: ATM):
        self.rec_mgr = rec_mgr
 
    def Health(self, request, context):
        hostname = socket.gethostname()
        os_version = "Windows 11"  # you can query real version if you want
        teams_running = False      # you said Teams control is done; hook your check here
        return pb2.HealthResponse(
            hostname=hostname,
            os_version=os_version,
            teams_running=teams_running,
        )
    def PrepareRecording(self, request, context):
        try:
            if not self.rec_mgr.prepare(run_id=request.run_id):
                return pb2.PrepareRecordingResponse(ok=False, message='Fail to join the teams call meeting!')  
            return pb2.PrepareRecordingResponse(ok=True, message="READY")
        except Exception as e:
            return pb2.PrepareRecordingResponse(ok=False, message=str(e))

    def StartRecording(self, request, context):
        try:
            out_path = self.rec_mgr.start(request.run_id, request.mode)
            return pb2.StartRecordingResponse(ok=True, message="RECORDING", out_path=out_path)
        except Exception as e:
            return pb2.StartRecordingResponse(ok=False, message=str(e), out_path="")

    def StopRecording(self, request, context):
        try:
            out_path = self.rec_mgr.stop(request.run_id, request.mode)
            size = os.path.getsize(out_path)
            TC.end_meeting()
            return pb2.StopRecordingResponse(ok=True, message="STOPPED", out_path=out_path, bytes_written=size)
        except Exception as e:
            return pb2.StopRecordingResponse(ok=False, message=str(e), out_path="", bytes_written=0)
        
    def JoinMeetingByUrl(self, request, context):
        try:
            url = (request.meeting_url or "").strip()
            if not url:
                return pb2.JoinMeetingByUrlResponse(ok=False, message="meeting_url is empty")
            if not (url.startswith("http://") or url.startswith("https://")):
                return pb2.JoinMeetingByUrlResponse(ok=False, message="meeting_url must start with http(s)://")
            
            tc = TC(url,'teams_call')
            result = tc.open_teams_and_join_meeting()
            if not result:
                return pb2.JoinMeetingByUrlResponse(ok=False, message="Meeting join fail!")
            
            return pb2.JoinMeetingByUrlResponse(ok=True, message="Opened meeting URL")

        except Exception as e:
            return pb2.JoinMeetingByUrlResponse(ok=False, message=str(e))
    def OpenUrl(self, request, context):
        try:
            url = request.url.strip()
            if not (url.startswith("http://") or url.startswith("https://")):
                return pb2.OpenUrlResponse(ok=False, message="URL must start with http:// or https://")
            webbrowser.open(url, new=1 if request.new_window else 0)
            return pb2.OpenUrlResponse(ok=True, message="Opened")
        except Exception as e:
            return pb2.OpenUrlResponse(ok=False, message=str(e))

    def DownloadFile(self, request, context):
        path = request.path
        chunk_size = request.chunk_size or 262144 #256k

        if not os.path.isfile(path):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"File not found: {path}")
            return 
        with open(path, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield pb2.FileChunk(data=data)
    
    def CloseTeamsMeeting(self, request: empty_pb2.Empty, context):
        try:
            # close the meeting
            TC.close_teams()
            return pb2.SimpleResponse(ok=True, message="Teams meeting closed")
        except Exception as e:
            return pb2.SimpleResponse(ok=False, message=str(e))

    def CloseUrl(self, request: empty_pb2.Empty, context):
        try:
            # kill all webbrowser
            Utils.taskkill("msedge.exe")
            Utils.taskkill("chrome.exe")
            return pb2.SimpleResponse(ok=True, message="Meeting URL closed")
        except Exception as e:
            return pb2.SimpleResponse(ok=False, message=str(e))


    def GetHeadsetStatus(self, request, context):
        try:
            devs = hsc._sd_devices()
            default_in, default_out = hsc._sd_default_indices() 
            mics, spks = hsc._match_by_hint(devs, request.name_hint) 
            # If user provided name_hint, presence means matched list is non-empty.
            # If name_hint empty, presence means default device exists.
            if (request.name_hint or "").strip():
                mic_present = len(mics) > 0
                speaker_present = len(spks) > 0
            else:
                mic_present = default_in is not None and default_in >= 0
                speaker_present = default_out is not None and default_out >= 0

            # Determine overall
            if request.require_mic or request.require_speaker:
                headset_present = (not request.require_mic or mic_present) and \
                                 (not request.require_speaker or speaker_present)
            else:
                headset_present = mic_present or speaker_present
            # Default endpoints
            default_mic = pb2.AudioEndpoint()
            default_speaker = pb2.AudioEndpoint()
            if default_in is not None and 0 <= default_in < len(devs):
                default_mic = hsc._mk_endpoint(default_in, devs[default_in]["name"], True)
            if default_out is not None and 0 <= default_out < len(devs):
                default_speaker = hsc._mk_endpoint(default_out, devs[default_out]["name"], True)
            resp = pb2.HeadsetStatusResponse(
                ok=True,
                message="OK",
                headset_present=headset_present,
                mic_present=mic_present,
                speaker_present=speaker_present,
                default_mic=default_mic,
                default_speaker=default_speaker,
            )
            # Matched lists (only meaningful when name_hint set, but okay to return anyway)
            for idx, name in mics:
                resp.matched_mics.append(hsc._mk_endpoint(idx, name, idx == default_in))
            for idx, name in spks:
                resp.matched_speakers.append(hsc._mk_endpoint(idx, name, idx == default_out))

            return resp

        except Exception as e:
            return pb2.HeadsetStatusResponse(ok=False, message=str(e))
      
def audio_folder_checking():
    path = Path("audio") 
    if not path.exists():
        os.makedirs("audio")
        print("Created audio folder...")


def serve(bind_addr="0.0.0.0:50051"):
    rec_mgr = ATM()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_DutAgentServicer_to_server(DutAgent(rec_mgr), server)
    server.add_insecure_port(bind_addr)
    server.start()
    print(f"DUT Agent listening on {bind_addr}")
    server.wait_for_termination()

if __name__ == "__main__":
    audio_folder_checking()
    serve()
