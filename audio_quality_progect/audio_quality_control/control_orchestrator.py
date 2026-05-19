import asyncio
import os
import time
import grpc
import audio_test_pb2 as pb2
import audio_test_pb2_grpc as pb2_grpc
from google.protobuf import empty_pb2
from audio_control_manager import AudioControlManager as ACM
from teams_meeting_manager import MeetingControl as TC

DUT1_IP = "192.168.70.2:50051"
DUT2_IP = "192.168.70.158:50051"

target_speaker = "USBAudio2.0"
audio_path = r"sound_resource\POLQA-F1-S1-48k.wav"


meeting_url = "https://teams.microsoft.com/l/meetup-join/19%3ameeting_NmMxZWE4NDEtODg0YS00YTZhLWE1NTMtNmIzZDlkMThjNWM5%40thread.v2/0?context=%7b%22Tid%22%3a%224d5ee319-c659-429d-bc2f-71fd32fb7d9f%22%2c%22Oid%22%3a%2277f53215-d585-40ba-a9d2-d47315d51447%22%7d"
youtube_url = "https://www.youtube.com/watch?v=PyD9cMarVJk"

headset_target = "poly"

async def download_file(stub, remote_path: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    resp_stream = stub.DownloadFile(pb2.DownloadFileRequest(path=remote_path, chunk_size=262144))

    with open(local_path, "wb") as f:
        async for chunk in resp_stream:
            f.write(chunk.data)


async def safe_call(step_name: str, call_factory, fatal: bool = True):
    """Execute one RPC step and handle transport/app-level failures consistently."""
    try:
        resp = await call_factory()
    except grpc.aio.AioRpcError as exc:
        print(f"[ERROR] {step_name}: RPC failed ({exc.code().name}) {exc.details()}")
        if fatal:
            raise
        return None
    except Exception as exc:
        print(f"[ERROR] {step_name}: unexpected failure: {exc}")
        if fatal:
            raise
        return None

    if hasattr(resp, "ok") and not resp.ok:
        message = getattr(resp, "message", "No message")
        print(f"[ERROR] {step_name}: operation reported failure: {message}")
        if fatal:
            raise RuntimeError(f"{step_name} failed: {message}")

    return resp


async def print_headset_status(stub, dut_name: str):
    resp = await safe_call(
        f"{dut_name} GetHeadsetStatus",
        lambda: stub.GetHeadsetStatus(
            pb2.HeadsetStatusRequest(
                name_hint=headset_target,
                require_mic=True,
                require_speaker=True,
            ),
            timeout=5,
        ),
        fatal=False,
    )
    if not resp:
        return

    print(f"[{dut_name}] headset present: {resp.headset_present}")
    print(f"[{dut_name}] default mic: {resp.default_mic.name}")
    print(f"[{dut_name}] default speaker: {resp.default_speaker.name}")


async def prepare_recording_with_retry(stub, run_id: str, retries: int = 3, retry_delay_s: int = 2):
    """Prepare recording with retries to absorb transient DUT readiness/RPC failures."""
    last_message = "unknown error"

    for attempt in range(1, retries + 1):
        prep = await safe_call(
            f"DUT2 PrepareRecording (attempt {attempt}/{retries})",
            lambda: stub.PrepareRecording(
                pb2.PrepareRecordingRequest(run_id=run_id),
                timeout=20,
            ),
            fatal=False,
        )

        if prep and getattr(prep, "ok", False):
            return prep

        if prep is not None:
            last_message = getattr(prep, "message", last_message)
        else:
            last_message = "RPC transport or unexpected error"

        if attempt < retries:
            print(f"[WARN] DUT2 PrepareRecording failed, retry in {retry_delay_s}s...")
            await asyncio.sleep(retry_delay_s)

    raise RuntimeError(f"[DUT2] Prepare failed after {retries} attempts: {last_message}")

async def main():
    run_id = time.strftime("Run_%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), "record", run_id)
    os.makedirs(out_dir, exist_ok=True)

    channel_1 = grpc.aio.insecure_channel(DUT1_IP)
    channel_2 = grpc.aio.insecure_channel(DUT2_IP)
    acm = None
    tc = None
    stub_2 = None
    local_teams_joined = False
    dut2_recording_started = False
    stop_mic = None

    try:
        acm = ACM()
    except Exception as exc:
        print(f"[WARN] AudioControlManager not available, audio playback will be skipped: {exc}")

    try:
        # create stub for both channels
        stub_1 = pb2_grpc.DutAgentStub(channel_1)
        stub_2 = pb2_grpc.DutAgentStub(channel_2)

        # check both channels first
        health_1 = await safe_call(
            "DUT1 Health",
            lambda: stub_1.Health(pb2.HealthRequest(), timeout=3),
            fatal=True,
        )
        print(f"[{DUT1_IP}] hostname={health_1.hostname}, os={health_1.os_version}")

        health_2 = await safe_call(
            "DUT2 Health",
            lambda: stub_2.Health(pb2.HealthRequest(), timeout=3),
            fatal=True,
        )
        print(f"[{DUT2_IP}] hostname={health_2.hostname}, os={health_2.os_version}")

        # step 1: DUT1 opens YouTube and verify headset status
        # open youtube url
        resp = await safe_call(
            "DUT1 OpenUrl",
            lambda: stub_1.OpenUrl(
                pb2.OpenUrlRequest(
                    url=youtube_url,
                    new_window=True,
                    bring_to_front=False,
                ),
                timeout=10,
            ),
            fatal=True,
        )
        print(resp.ok, resp.message)

        # Start control-side Teams meeting before DUT2 joins.
        tc = TC(meeting_url, "teams_call")
        result = await asyncio.to_thread(tc.open_teams_and_join_meeting)
        if not result:
            raise RuntimeError("Control-side Teams meeting join failed")
        local_teams_joined = True

        # check dut1 headset status
        print("check dut1 headset status:")
        await print_headset_status(stub_1, "DUT1")

        # step 3: DUT2 opens Teams meeting and verify headset status
        print("open teams call and join meeting")
        resp = await safe_call(
            "DUT2 JoinMeetingByUrl",
            lambda: stub_2.JoinMeetingByUrl(
                pb2.JoinMeetingByUrlRequest(meeting_url=meeting_url, open_in_new_window=True),
                timeout=300,
            ),
            fatal=True,
        )
        print(resp.ok, resp.message)

        # Check dut2 headset status before audio recording
        print("check dut2 headset status:")
        await print_headset_status(stub_2, "DUT2")

        # dut2 prepares recording
        await prepare_recording_with_retry(stub_2, run_id)


        # dut2 starts recording
        started = await safe_call(
            "DUT2 StartRecording",
            lambda: stub_2.StartRecording(
                pb2.StartRecordingRequest(run_id=run_id, mode=pb2.MIC),
                timeout=20,
            ),
            fatal=True,
        )
        dut2_recording_started = bool(started and getattr(started, "ok", False))

        # wait for 3 sec
        print("waiting for 3 sec")
        await asyncio.sleep(3)

        # after meeting starts, play reference audio via AudioControlManager
        if acm:
            try:
                acm.play_audio_file(target_speaker, audio_path, block=True)
            except Exception as exc:
                print(f"[WARN] audio playback failed: {exc}")

            
        # stop recording
        stop_mic = await safe_call(
            "DUT2 StopRecording",
            lambda: stub_2.StopRecording(
                pb2.StopRecordingRequest(run_id=run_id, mode=pb2.MIC),
                timeout=30,
            ),
            fatal=True,
        )
        dut2_recording_started = False
       

        # step 4: close DUT2 meeting, then verify DUT1 headset status again
        # close dut2 teams call meeting
        print("close dut2 teams call meeting")
        await safe_call(
            "DUT2 CloseTeamsMeeting",
            lambda: stub_2.CloseTeamsMeeting(empty_pb2.Empty(), timeout=10),
            fatal=False,
        )

        # wait for 10 sec
        print("wait for 10 sec")
        await asyncio.sleep(10)

        print("check dut1 headset status:")
        await print_headset_status(stub_1, "DUT1")

        # close URL on dut1 (best effort)
        await safe_call(
            "DUT1 CloseUrl",
            lambda: stub_1.CloseUrl(empty_pb2.Empty(), timeout=10),
            fatal=False,
        )

        #download audio file
        remote_path = getattr(stop_mic, "out_path", "") if stop_mic else ""
        if remote_path:
            local_a = os.path.join(out_dir, "dut2_tx_mic.wav")
            await safe_call(
                "DUT2 DownloadFile",
                lambda: download_file(stub_2, remote_path, local_a),
                fatal=True,
            )
            print("Downloaded:")
            print(" ", local_a)
        else:
            print("[WARN] DUT2 StopRecording returned empty out_path, skip download")

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
    except Exception as exc:
        print(f"[FATAL] test flow aborted: {exc}")
    finally:
        if dut2_recording_started and stub_2:
            try:
                await safe_call(
                    "DUT2 StopRecording (finalizer)",
                    lambda: stub_2.StopRecording(
                        pb2.StopRecordingRequest(run_id=run_id, mode=pb2.MIC),
                        timeout=20,
                    ),
                    fatal=False,
                )
            except Exception:
                pass

        if acm:
            acm.stop_audio()
        if tc and local_teams_joined:
            try:
                await asyncio.to_thread(TC.end_meeting)
            except Exception as exc:
                print(f"[WARN] local Teams end_meeting failed: {exc}")

            try:
                await asyncio.to_thread(TC.close_teams)
            except Exception as exc:
                print(f"[WARN] local Teams close_teams failed: {exc}")

        await asyncio.gather(
            channel_1.close(),
            channel_2.close(),
            return_exceptions=True,
        )
    

if __name__ == "__main__":
    asyncio.run(main())
