import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Union
import xml.etree.ElementTree as ET 
from Evtx.Evtx import Evtx
from typing import List , Iterable
import os

# XML namespace for Windows event logs
NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}

# filter event list

EVENT_LIST = {
1863 :"BT_WEV_DEVICE_IO_TX_TIMEOUT",
1864 :"BT_WEV_DEVICE_IO_RX_TIMEOUT",
1857 :"IBTPCI_BT_WEV_BRI_CONFIG_FAILED",
1877 :"IBTPCI_BT_WEV_CFA_ADV_START_FAIL_ID",
1878 :"IBTPCI_BT_WEV_CFA_ADV_STOP_FAIL_ID",
#1902 :"IBTPCI_BT_WEV_CFA_ADV_START_ID",
#1903 :"IBTPCI_BT_WEV_CFA_ADV_STOP_ID",
1904 :"IBTPCI_BT_WEV_FW_ROM_TX_TIMEOUT",
1905 :"IBTPCI_BT_WEV_FW_ROM_RX_TIMEOUT",
1866 :"BT_WEV_PRODUCT_RESET_FAILED",
1867 :"IBPCI_BT_WEV_FIPS_ERROR",
1871 :"BT_CORE_RESET(FLDR)_PERFORMED",
1872 :"PRODUCT_RESET_TRIGGERED",
1873 :"PRODUCT_RESET_REGUESTED",
1874 :"SENSOR_REGISTRATION_FAILED",
1819 :"FATAL_EXCEPTION_EVENT",
1820 :"SYSTEM_EXCEPTION_EVENT",
1840 :"USB_TRANSACTION_ERROR_EVENT",
1841 :"USB_NO_SUCH_DEVICE_EVENT",
1842 :"STATUS_IO_TIMEOUT_EVENT",
1851 :"FW_VALODATION_FAILED_EVENT",
1852 :"FW_DOWNLOAD_FAILED_EVENT",
1853 :"FW_RESET_FAILED_EVENT",
1854 :"FW_INVAILED_META_DATA",
1855 :"FW_FSEQ_ERROR_EVENT",
1856: "DRIVER_LOAD_IS_BLOCKED_DUE_TO_SECURITY_REASONS"
}


def _to_utc(dt_or_str: Union[datetime, str]) -> datetime:
    """
    Convert a datetime or 'YYYY-MM-DD HH:MM:SS' string (local time)
    into an aware UTC datetime.
    """
    if isinstance(dt_or_str, datetime):
        dt = dt_or_str
    elif isinstance(dt_or_str, str):
        dt = datetime.strptime(dt_or_str, "%Y-%m-%d %H:%M:%S")
    else:
        raise TypeError("Time must be datetime or 'YYYY-MM-DD HH:MM:SS' string") 
    # If no timezone info, assume local time
    if dt.tzinfo is None:
        dt = dt.astimezone()  # attach local tz 
    return dt.astimezone(timezone.utc)


def export_system_log_time_range(
    start_time: Union[datetime, str],
    end_time: Union[datetime, str],
    save_path: Union[str, Path],
) -> bool:
    """
    Export Windows 'System' event log from a specific time period into a .evtx file. 
    Parameters
    ----------
    start_time : datetime or str
        Start of time range (local time). If str, format: 'YYYY-MM-DD HH:MM:SS'.
    end_time   : datetime or str
        End of time range (local time). If str, format: 'YYYY-MM-DD HH:MM:SS'.
    save_path  : str or Path
        Destination .evtx path, e.g. 'C:\\Logs\\System_2025-01-10_09-12.evtx'. 
    Returns
    -------
    bool
        True if export looks successful, False otherwise.
    """
    try:
        start_utc = _to_utc(start_time)
        end_utc = _to_utc(end_time)
    except Exception as exc:
        print(f"[export_system_log_time_range] Invalid time: {exc}")
        return False

    if end_utc <= start_utc:
        print("[export_system_log_time_range] end_time must be after start_time")
        return False

    # Format: 2025-01-10T09:00:00.000Z
    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    start_str = fmt(start_utc)
    end_str = fmt(end_utc)

    # XPath query for TimeCreated in the range
    query = (
        f"*[System[TimeCreated[@SystemTime >= '{start_str}' and "
        f"@SystemTime <= '{end_str}']]]"
    )
    save_path = os.path.join(save_path,'system_event_log.evtx')
    save_path = Path(save_path)
  
    cmd = [
        "wevtutil",
        "epl",
        "System",
        str(save_path),
        "/q:" + query,
    ] 
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[export_system_log_time_range] 'wevtutil' not found. Run on Windows.")
        return False 
    if completed.returncode != 0:
        print("[export_system_log_time_range] wevtutil failed:")
        print(completed.stderr)
        return False
    return True


def export_system_log_last_seconds(
    duration_seconds: int,
    save_path: Union[str, Path],
) -> bool:
    """
    Export the Windows 'System' event log for the last `duration_seconds` seconds.

    Time range = [now - duration_seconds, now] in local time.

    Parameters
    ----------
    duration_seconds : int
        How many seconds back from now you want to capture.
        For example, 3600 means "last 1 hour".
    save_path : str or Path
        Destination .evtx path,
        e.g. 'C:\\Logs\\System_last_3600s.evtx'.

    Returns
    -------
    bool
        True if export looks successful, False otherwise.
    """
    if duration_seconds <= 0:
        print("[export_system_log_last_seconds] duration_seconds must be > 0")
        return False

    end_local = datetime.now().astimezone()
    start_local = end_local - timedelta(seconds=duration_seconds)
    return export_system_log_time_range(
        start_time=start_local,
        end_time=end_local,
        save_path=save_path,
    )
 

def filter_evtx_by_event_ids(
    evtx_path: Union[str, Path],
    event_ids: Iterable[int],
) -> List[str]:
    """
    Scan a .evtx file and return a list of event messages whose EventID
    is in the given list.

    Parameters
    ----------
    evtx_path : str or Path
        Path to the .evtx file (e.g. 'C:\\Logs\\System_last_1h.evtx').
    event_ids : Iterable[int]
        Event IDs to match, e.g. [41, 6008, 7000].

    Returns
    -------
    List[str]
        Each item is a human-readable string containing time, EventID,
        provider, level, computer, and record ID.
    """
    evtx_path = os.path.join(evtx_path,'system_event_log.evtx')
    evtx_path = Path(evtx_path)
    ids_set = {int(eid) for eid in event_ids}
    messages: List[str] = []

    if not evtx_path.exists():
        print(f"[filter_evtx_by_event_ids] File not found: {evtx_path}")
        return messages

    with Evtx(str(evtx_path)) as log:
        for record in log.records():
            try:
                xml_str = record.xml()
                root = ET.fromstring(xml_str)

                system = root.find("e:System", NS)
                if system is None:
                    continue 
                event_id_el = system.find("e:EventID", NS)
                if event_id_el is None or not event_id_el.text:
                    continue 
                try:
                    event_id = int(event_id_el.text) 
                except ValueError:
                    continue 
                if event_id not in ids_set: 
                    continue 
                # Extract basic info
                time_el = system.find("e:TimeCreated", NS)
                time_created = (
                    time_el.get("SystemTime") if time_el is not None else ""
                )
                msg = (
                    f"{time_created} | EventID={event_id} | Message={EVENT_LIST[event_id]} "
                )
                messages.append(msg)

            except Exception:
                
                # Skip malformed or unparsable records
                continue

    return messages



if __name__ == "__main__":
    
    ok = export_system_log_last_seconds(
        duration_seconds=7200,  # last 1 hour
        save_path=r"C:\Logs",
    )  
    print("Export success:", ok)
    
    if True:
        # 2. Filter by multiple error codes
        codes_to_find = EVENT_LIST
        events = filter_evtx_by_event_ids(
            r"C:\Logs",
            codes_to_find,
        )

        print(f"Found {len(events)} matching events.")
        for line in events:
            print(line)
  

