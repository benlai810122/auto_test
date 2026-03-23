import asyncio
import os
import time
import grpc 
import audio_test_pb2 as pb2
import audio_test_pb2_grpc as pb2_grpc
from google.protobuf import empty_pb2

DUT1_IP = "192.168.70.2:50051"
DUT2_IP = "192.168.70.158:50051"


meeting_url = "https://teams.microsoft.com/meet/21942003076107?p=rl8WJrKGgHXU8itu2u"
youtube_url = "https://www.youtube.com/watch?v=Kw1s1KlDqI0"

headset_target = "Poly"

async def download_file(stub, remote_path: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    resp_stream = stub.DownloadFile(pb2.DownloadFileRequest(path=remote_path, chunk_size=262144))

    with open(local_path, "wb") as f:
        async for chunk in resp_stream:
            f.write(chunk.data)

async def main():
    
    run_id = time.strftime("Run_%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), "record", run_id)
    channel_1 = grpc.aio.insecure_channel(DUT1_IP)
    channel_2 = grpc.aio.insecure_channel(DUT2_IP)
    
    try:
        # create stub for both channel:
        stub_1 = pb2_grpc.DutAgentStub(channel_1)
        stub_2 = pb2_grpc.DutAgentStub(channel_2) 
        
        
        
        # start with check both channel's status 
        health_1 = await stub_1.Health(pb2.HealthRequest(), timeout=3)
        print(f"[{DUT1_IP}] hostname={health_1.hostname}, os={health_1.os_version}")

        health_2 = await stub_2.Health(pb2.HealthRequest(), timeout=3)
        print(f"[{DUT1_IP}] hostname={health_2.hostname}, os={health_2.os_version}")

  
        # step 1: make sure dut_1 open the youtube and check the headset status:
        # open youtube url
        resp = await stub_1.OpenUrl(pb2.OpenUrlRequest(
            url=youtube_url,
            new_window=True,
            bring_to_front=False,
        ), timeout=10)
        print(resp.ok, resp.message)

        time.sleep(10)
        # check dut1 headset status
        print("check dut1 headset status:")
        resp = await stub_1.GetHeadsetStatus(pb2.HeadsetStatusRequest(
            name_hint=headset_target,
            require_mic=True,
            require_speaker=True,
        ), timeout=5)

        if not resp.ok:
            print("Error:", resp.message)
        else:
            print("Headset present:", resp.headset_present)
            print("Default mic:", resp.default_mic.name)
            print("Default speaker:", resp.default_speaker.name)
                 
        
        #step3: DUT2 open teams calls and join the meeting, and then check the headset status
        print("open teams call and join meeting")
        resp = await stub_2.JoinMeetingByUrl(
            pb2.JoinMeetingByUrlRequest(meeting_url=meeting_url, open_in_new_window=True),
            timeout=300,
        )
        print(resp.ok, resp.message)

        # wait for 15 sec
        print("waiting for 15 sec")
        time.sleep(15)
        
        # check dut2 headset status
        print("check dut2 headset status:")
        resp = await stub_2.GetHeadsetStatus(pb2.HeadsetStatusRequest(
            name_hint=headset_target,
            require_mic=True,
            require_speaker=True,
        ), timeout=5)

        if not resp.ok:
            print("Error:", resp.message)
        else:
            print("Headset present:", resp.headset_present)
            print("Default mic:", resp.default_mic.name)
            print("Default speaker:", resp.default_speaker.name)
        
        # wait for 15 sec
        print("waiting for 15 sec")
        time.sleep(15)
 
        #step4: dut2 close the meeting , and wait for 10 sec then check dut1 headset status
        
        # close dut2 teams call meeting
        print("close dut2 teams call meeting")
        resp = await stub_2.CloseTeamsMeeting(empty_pb2.Empty(), timeout=10)
        if not resp.ok:
             print(f"DUT2 CloseTeamsMeeting failed: {resp.message}")
        # wait for 1o sec
        print("wait for 10 sec")
        time.sleep(10)
        print("check dut1 headset status:")
        resp = await stub_1.GetHeadsetStatus(pb2.HeadsetStatusRequest(
            name_hint=headset_target,
            require_mic=True,
            require_speaker=True,
        ), timeout=5)

        if not resp.ok:
            print("Error:", resp.message)
        else:
            print("Headset present:", resp.headset_present)
            print("Default mic:", resp.default_mic.name)
            print("Default speaker:", resp.default_speaker.name)
        
        # close URL on dut1
        resp = await stub_1.CloseUrl(empty_pb2.Empty(), timeout=10)
        if not resp.ok:
            print(f"DUT1 CloseUrl failed: {resp.message}")

        '''
        prep = await stub_1.PrepareRecording(pb2.PrepareRecordingRequest(run_id=run_id))
        if not prep.ok:
            raise RuntimeError(f"[{dut_1}] Prepare failed: {prep.message}")


        # start recording
        started = await stub_1.StartRecording(pb2.StartRecordingRequest(run_id=run_id, mode=pb2.MIC))
        if not started.ok:
            raise RuntimeError(f"[{dut_1}] Start failed: {started.message}")
        # ... your test window ...
        await asyncio.sleep(30) 
        #TBH
        # stop recording
        stop_mic = await stub_1.StopRecording(pb2.StopRecordingRequest(run_id=run_id, mode=pb2.MIC), timeout=20)

        #download audio file
        local_a = os.path.join(out_dir, "tx_mic.wav")
        await download_file(stub_1, stop_mic.out_path, local_a)
        print("Downloaded:")
        print(" ", local_a)
        '''
    finally:
        await channel_1.close()
        await channel_2.close()
    

if __name__ == "__main__":
    asyncio.run(main())
