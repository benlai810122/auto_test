"""
script responsible for all the DUT functionality
"""

import xmlrpc.server
from vpt_contoller import VPTControl


class VPTServer:
    """
    class responsible for all the server functionality on the DUT
    """
    def vpt_bot_join(self) -> bool:
        """
        The function is invoked upon the completion of the test.
        """
        vptcontrol = VPTControl()
        return vptcontrol.vpt_bot_join()
    
    def vpt_bot_close(self) -> None:
      
        VPTControl.vpt_bot_close()
        return True


class RequestHandler(xmlrpc.server.SimpleXMLRPCRequestHandler):
    rpc_paths = "/RPC2"

    def log_message(self, format: str, *args) -> None:
        pass

    # return super().log_message(format, *args)


def main() -> None:
    """
    main entry point to the DUT server
    """
    # get the LAN IP address
    lan_ip_address = "127.0.0.1"

    # get the listen port
    listen_port = 8001

    # start the server
    server = xmlrpc.server.SimpleXMLRPCServer(
        (lan_ip_address, listen_port), requestHandler=RequestHandler, allow_none=True
    )
    server.register_instance(VPTServer())

    print(f"starting server ip {lan_ip_address} port: {listen_port} ..")
    server.serve_forever()


if __name__ == "__main__":
    main()
