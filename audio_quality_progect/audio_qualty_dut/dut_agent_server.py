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
