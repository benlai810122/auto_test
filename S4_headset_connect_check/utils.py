"""
global parameters manager, based on config.json
"""

import json
import logging
from subprocess import PIPE, Popen
from logging.handlers import RotatingFileHandler
import os
import time
import argparse
import re
import socket
import subprocess
import zipfile

# pylint: disable=logging-fstring-interpolation


# must be first, since used for ROOT_FOLDER which is responsive for all the automation
def get_workspace() -> str:
    """
    returns the workspace "ROOT_DIR" function
    needed for unit test purposes, when automation is not really run on the real setup
    """
    # in operational mode, this path should exist
    # if not IS_TEST_MODE:
    # assert os.path.isdir(DEFAULT_WORKSPACE), f"{DEFAULT_WORKSPACE} doesn't exit - cannot proceed"
    # return DEFAULT_WORKSPACE

    # in test mode, run the script from here
    return os.path.dirname(__file__)


"""
def is_test_mode() -> bool:
    returns True in case this is a debug/test mode run and False otherwise
    parser = argparse.ArgumentParser(description="Power Consumption")
    parser.add_argument("-tm", "--test-mode", action="store_true", required=False, help="debug/test mode is enabled")
    params = parser.parse_args()
    return params.test_mode
"""

# test mode will define the workspace
# IS_TEST_MODE = is_test_mode()

# folder of all the service files
# do not use relative paths since once service is running, it will not run from here
DEFAULT_WORKSPACE = "c:/power_consumption/dut_server"
ROOT_FOLDER = get_workspace()

JSON_FILES_FOLDER = os.path.join(ROOT_FOLDER, "json_files")

# Python Log
PYTHON_LOG_FILE = os.path.join(ROOT_FOLDER, "log.txt")

# json file for service info (must have absolute path since called from service different path)
SERVICE_FILE_PATH = os.path.join(JSON_FILES_FOLDER, "service.json")

# json file for app configuration
CONFIG_FILE_PATH = os.path.join(JSON_FILES_FOLDER, "dut_config.json")

# tasks should be killed before testing
TASK_LIST = ["one", "msed", "team", "ms-team", "hp", "office"]

# window updated services should be stop before testing
SERVICE_LIST = ["wuauserv", "UsoSvc"]

# Rotating logger + stdout to CLI
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] <%(filename)s> %(funcName)s() %(message)s",
    handlers=[
        RotatingFileHandler(PYTHON_LOG_FILE, maxBytes=10000000, backupCount=1),
        logging.StreamHandler(),
    ],
)


log = logging.getLogger("POWER CONSUMPTION")


class Service:
    """
    responsible to get all parameters from service json and return them
    """

    def __init__(self):
        """
        CTOR, json file and fill global variables
        """
        log.info("Service class CTOR is called")
        self.__config_json_name = SERVICE_FILE_PATH

        with open(self.__config_json_name, mode="r", encoding="utf8") as file:
            data = json.load(file)

            # fill parameters
            self.service_name = data["service_name"]
            self.service_display_name = data["service_display_name"]
            self.service_description = data["service_description"]
            self.startup = data["startup"]
            self.username = data["username"]
            self.password = data["password"]

    def __del__(self):
        """
        DTOR, do nothing
        """
        log.info("Service class DTOR is called")


class Utils:
    """
    static class for utils functions
    """

    # store the LAN adapter name
    # do not call this variable directly, use get_adapter_name()
    __adapter_name = ""

    @staticmethod
    def run_sync_cmd(cmd, get_stdout=False) -> str:
        """
        function runs a given cli cmd synchronously and returns the stdout (if required)
        """
        #log.info(f">> {cmd}")

        # set stdout value based on caller request
        stdout = PIPE if get_stdout else None

        # start the process
        proc = Popen(cmd, stdout=stdout)

        # wait for process to finish
        proc.wait()

        if not get_stdout:
            return None

        return proc.communicate()[0].decode("utf-8")

    @staticmethod
    def run_sync_ps_cmd(cmd) -> str:
        """
        function runs a given cli power shell synchronously and returns the stdout
        """
        return Utils.run_sync_cmd(f"powershell -Command {cmd}", get_stdout=True)

    @staticmethod
    def sleep_sec(sleep_time_sec: int) -> None:
        """
        function performs time.sleep, however, in case of test mode returns immediately
        """
        # if not IS_TEST_MODE:
        time.sleep(sleep_time_sec)

    @staticmethod
    def get_adapter_name() -> str:
        """
        returns the LAN adapter name
        """
        if not Utils.__adapter_name:
            res = Utils.run_sync_ps_cmd(
                'Get-NetAdapter -Physical | Format-List -Property "Name","MediaType"'
            )
            # filter LAN only (802.3)
            if match := re.findall(
                r"Name\s+:\s+([^\r\n]+)\s+MediaType\s+:\s+802.3", res
            ):
                # verify we have only one
                if len(match) == 1:
                    log.info("Ethernet name = " + match[0])
                    Utils.__adapter_name = match[0]
                else:
                    log.info(f"found {len(match)} LAN adapters, which one to disable?")
            else:
                log.info("no LAN adapter was found")

        return Utils.__adapter_name

    @staticmethod
    def disable_lan() -> None:
        """
        function disables the LAN (or USB to LAN)
        """
        log.info("disable LAN adapter")

        Utils.run_sync_ps_cmd(
            f"Disable-NetAdapter -Name '{Utils.get_adapter_name()}' -confirm:$false"
        )

    @staticmethod
    def enable_lan() -> None:
        """
        function enables the LAN (or USB to LAN)
        """
        log.info("enable LAN adapter")

        Utils.run_sync_ps_cmd(
            f"Enable-NetAdapter -Name '{Utils.get_adapter_name()}' -confirm:$false"
        )

    @staticmethod
    def get_local_lan_ip_address() -> str:
        """
        returns the local LAN IP address
        """
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("192.168.1.1", 80))
        socketname = temp_socket.getsockname()[0]
        temp_socket.close()
        return socketname

    @staticmethod
    def get_wlan_ip_address() -> str:
        """
        returns the local LAN IP address
        """
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))
        socketname = temp_socket.getsockname()[0]
        temp_socket.close()
        return socketname

    @staticmethod
    def get_server_listen_port() -> int:
        """
        returns the server listen port
        """
        # at this point, hardcoded
        # TODO: get from some conf file
        return 8000

    @staticmethod
    def winserv_close(serviceName: str) -> str:
        """
        CTOR, json file and fill global variables
        """
        result = Utils.run_sync_cmd(f"sc stop {serviceName}")
        return result

    @staticmethod
    def taskkill(taskname: str) -> str:
        result = Utils.run_sync_cmd(f"taskkill /im {taskname}* /f")
        return result

    @staticmethod
    def zip_subfolders(source_folder, zip_name):
        """
        Zip all the folders within the specified directory.
        """
        with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for item in os.listdir(source_folder):
                item_path = os.path.join(source_folder, item)
                if os.path.isdir(item_path):
                    print(
                        f"Zipping folder: {item_path}"
                    )  # Print which folder is being zipped
                    for root, _, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            print(f"file_path and file [{file_path}], [{file}]")
                            zipf.write(
                                file_path, os.path.relpath(file_path, source_folder)
                            )

    @staticmethod
    def send_folder(server_ip, server_port, source_folder):
        """
        Send all the files in a specified folder to a specified socket server.
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))

        folder_name = os.path.basename(source_folder)
        client_socket.send(folder_name.encode())
        response = client_socket.recv(1024).decode()
        print(response)

        for root, dirs, files in os.walk(source_folder):
            # only send the files in source folder root
            rel_dir = os.path.relpath(root, source_folder)
            if rel_dir == ".":
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, source_folder)
                    client_socket.send(rel_path.encode())
                    print(f"Sending file: {rel_path}")
                    # response = client_socket.recv(1024).decode()
                    # print(response)
                    with open(file_path, "rb") as f:
                        while True:
                            file_data = f.read(1024)
                            if not file_data:
                                break
                            client_socket.send(file_data)
                    client_socket.send(b"END_FILE")
                    response = client_socket.recv(1024).decode()
                    print(f"Control PC: {response}")
        client_socket.send(b"END_FOLDER")
        client_socket.close()


if __name__ == "__main__":
    ip_address = Utils.get_local_lan_ip_address()
    print(ip_address)
