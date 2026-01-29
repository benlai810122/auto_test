import asyncio
import os
import time
import grpc 
import audio_test_pb2 as pb2
import audio_test_pb2_grpc as pb2_grpc

async def download_file(stub, remote_path: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    resp_stream = stub.DownloadFile(pb2.DownloadFileRequest(path=remote_path, chunk_size=262144))

    with open(local_path, "wb") as f:
        async for chunk in resp_stream:
            f.write(chunk.data)

 
async def main():
    dut_mic = "192.168.70.100:50051"  # MIC
    dut_loopback = "10.0.0.102:50051"  # LOOPBACK 
    run_id = time.strftime("Run_%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), "record", run_id)
    channel_a = grpc.aio.insecure_channel(dut_mic)
    
    try:
        stub_a = pb2_grpc.DutAgentStub(channel_a) 
        health = await stub_a.Health(pb2.HealthRequest(), timeout=3)
        print(f"[{dut_mic}] hostname={health.hostname}, os={health.os_version}") 
        # prepare
        prep = await stub_a.PrepareRecording(pb2.PrepareRecordingRequest(run_id=run_id))
        if not prep.ok:
            raise RuntimeError(f"[{dut_mic}] Prepare failed: {prep.message}")
        # start recording
        started = await stub_a.StartRecording(pb2.StartRecordingRequest(run_id=run_id, mode=pb2.MIC))
        if not started.ok:
            raise RuntimeError(f"[{dut_mic}] Start failed: {started.message}")
        # ... your test window ...
        await asyncio.sleep(30) 
        #TBH
        # stop recording
        stop_mic = await stub_a.StopRecording(pb2.StopRecordingRequest(run_id=run_id, mode=pb2.MIC), timeout=20)

        #download audio file
        local_a = os.path.join(out_dir, "tx_mic.wav")
        await download_file(stub_a, stop_mic.out_path, local_a)
        print("Downloaded:")
        print(" ", local_a)
    finally:
        await channel_a.close()
    

if __name__ == "__main__":
    asyncio.run(main())
