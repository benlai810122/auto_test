import sounddevice as sd
import audio_test_pb2 as pb2


def refresh_sounddevice():
    # Private APIs but commonly used for this exact issue
    sd._terminate()
    sd._initialize()

def _sd_devices():
    refresh_sounddevice()
    return sd.query_devices()

def _sd_default_indices():
    try:
        di, do = sd.default.device  # (input, output)
        return di, do
    except Exception:
        return None, None

def _mk_endpoint(idx: int, name: str, is_default: bool):
    return pb2.AudioEndpoint(
        device_id=str(idx),
        name=name,
        is_default=is_default,
        is_enabled=True,  # sounddevice doesn't expose disabled state
    )

def _match_by_hint(devs, hint: str):
    hint = (hint or "").strip().lower()
    mics = []
    spks = []

    for idx, d in enumerate(devs):
        name = str(d.get("name", ""))
        if hint and hint not in name.lower():
            continue

        if d.get("max_input_channels", 0) > 0:
            mics.append((idx, name))
        if d.get("max_output_channels", 0) > 0:
            spks.append((idx, name))

    return mics, spks

if __name__ == "__main__":
    #for testing
    dev = _sd_devices()
    print(_sd_default_indices())
    print(_mk_endpoint(1, "Dell WL5024", True))
    print(_match_by_hint(dev,"Dell WL5024"))
