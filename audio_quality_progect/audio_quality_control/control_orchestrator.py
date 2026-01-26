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

async def start_recording(host: str, mode: int, run_id: str, out_dir: str):
    async with grpc.aio.insecure_channel(host) as channel:
        stub = pb2_grpc.DutAgentStub(channel)

        health = await stub.Health(pb2.HealthRequest(), timeout=3)
        print(f"[{host}] hostname={health.hostname}, os={health.os_version}")

        prep = await stub.PrepareRecording(
            pb2.PrepareRecordingRequest(
                run_id=run_id,
                mode=mode,
                device_id="default",
                sample_rate=48000,
                channels=2,
            ),
            timeout=10,
        )
        if not prep.ok:
            raise RuntimeError(f"[{host}] Prepare failed: {prep.message}")

        start_ms = int(time.time() * 1000)
        started = await stub.StartRecording(
            pb2.StartRecordingRequest(run_id=run_id, mode=mode, start_epoch_ms=start_ms),
            timeout=10,
        )
        if not started.ok:
            raise RuntimeError(f"[{host}] Start failed: {started.message}")

        return stub, started.out_path  # keep stub+path so we can stop+download later

async def main():
    dut_mic = "10.0.0.101:50051"  # MIC
    dut_loopback = "10.0.0.102:50051"  # LOOPBACK

    run_id = time.strftime("Run_%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), "record", run_id)

    # for testing
    stub_a, path_a = await start_recording(dut_mic, pb2.MIC, run_id, out_dir)

    # Start both recorders
    '''
    (stub_a, path_a), (stub_b, path_b) = await asyncio.gather(
        start_recording(dut_mic, pb2.MIC, run_id, out_dir),
        start_recording(dut_loopback, pb2.LOOPBACK, run_id, out_dir),
    ) 
    '''
    
    print("Both DUTs are recording. (Your Teams call/audio stimulus runs now)")
    await asyncio.sleep(10)  # replace with your real call window / stimulus timing
 
    """
    # control arduino start play 1k tone
    TBD.

    """ 
    # Stop both
    '''
    stop_mic, stop_loopback = await asyncio.gather(
        stub_a.StopRecording(pb2.StopRecordingRequest(run_id=run_id, mode=pb2.MIC), timeout=10),
        stub_b.StopRecording(pb2.StopRecordingRequest(run_id=run_id, mode=pb2.LOOPBACK), timeout=10),
    )
    '''  
    stop_mic = await stub_a.StopRecording(
    pb2.StopRecordingRequest(run_id=run_id, mode=pb2.MIC),
    timeout=10,)
    
    if not stop_mic.ok:
        raise RuntimeError(f"DUT-A stop failed: {stop_mic.message}")
     
    # Download both WAVs
    local_a = os.path.join(out_dir, "tx_mic.wav")
    local_b = os.path.join(out_dir, "rx_loopback.wav") 

    await download_file(stub_a, stop_mic.out_path, local_a)
    '''
    await asyncio.gather(
        download_file(stub_a, stop_mic.out_path, local_a),
        download_file(stub_b, stop_loopback.out_path, local_b),
    )
    ''' 
    print("Downloaded:")
    print(" ", local_a)
    print(" ", local_b)

if __name__ == "__main__":
    asyncio.run(main())
