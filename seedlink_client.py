import threading
from obspy.clients.seedlink.easyseedlink import create_client
from src.tools.Device import Device
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json


class DeviceBuffer:
    def __init__(self, maxlen=20):
        self.seq = 0
        self.deque = deque(maxlen=maxlen)

    def add_data(self, data):
        self.deque.append((self.seq, data))
        self.seq += 1

    def json(self):
        return json.dumps(tuple(self.deque))


class SeisCompClient:
    def __init__(self, server_address: str, streams: tuple[str, str, str], debug=False):
        super().__init__()
        self.server_address = server_address
        self.debug = debug
        self.queues: dict[tuple[str, str], DeviceBuffer] = {}
        self.streams = streams
        self.devices: dict[tuple, Device] = {}
        self.create_clients()

    def handle_data(self, trace):
        """
        Handles incoming trace data.

        :param trace: An object of class obspy.core.trace.Trace.
        """

        try:
            if self.debug:
                print(f"trace : {trace.__dict__}")

            device_id = (trace.stats.network, trace.stats.station)
            # add new device if not already exists
            if device_id not in self.devices.keys():
                self.devices[device_id] = Device(trace=trace)
                self.queues[device_id] = DeviceBuffer()

            self.devices[device_id].add_one_channel_packet(trace)

            serialized_output_packet = self.devices[
                device_id
            ].get_last_packet_if_completed_with_all_channels(serialize=True)
            if self.debug:
                print(serialized_output_packet)
            if serialized_output_packet is not None:
                if self.debug:
                    print("Sending data...")
                self.queues[device_id].add_data(serialized_output_packet)
        except Exception as e:
            print(f"Handle data exception: {e}")

    def create_clients(self):
        self.clients = []
        for network, station, selector in self.streams:
            client = create_client(self.server_address, on_data=self.handle_data)
            client.select_stream(network, station, selector)
            self.clients.append(client)

    def process_client(self, client):
        try:
            client.run()
        except Exception as e:
            print(f"Failed to connect to SeedLink server: {e}")

    def run(self) -> None:
        while True:
            for client in self.clients:
                self.process_client(client)


def start_client():
    server_address: str = "192.168.0.105:18000"
    streams: list[tuple[str, str, str]] = [
        # ('XX', '15', 'CXZ'),
        ("XX", "15", "CX?"),
        # ('XX', '18', 'CX?'),
        # ('XX', '37', 'CX?'),
        # ('XX', '38', 'CX?'),
        # ('YY', '39', 'CYZ'),
        # Add more streams as needed
    ]
    debug = False
    client = SeisCompClient(server_address=server_address, streams=streams, debug=False)
    thread = threading.Thread(target=client.run).start()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            if parsed.path.startswith("/data"):
                splitted = parsed.path.split("/")[2:]
                device_network, device_id = splitted
                self.wfile.write(
                    client.queues[(device_network, device_id)].json().encode("utf-8")
                )
            elif parsed.path == "/devices":
                self.wfile.write(
                    json.dumps(tuple(client.devices.keys())).encode("utf-8")
                )
            return

    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()


if __name__ == "__main__":
    start_client()
