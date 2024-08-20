import multiprocessing
import threading
import time
from obspy.clients.seedlink.easyseedlink import create_client
from obspy import Stream, Trace
import numpy as np
import requests
from classes import Device


class SeisCompClient(multiprocessing.Process):
    def __init__(self, server_address,
                 streams,
                 queue,
                 destination_web_server_post_url='http://127.0.0.1:5000/update_signal',
                 max_seiscomp_connection_retries=5,
                 connection_retry_delay=5,
                 debug=False):
        super().__init__()
        self.server_address = server_address
        self.destination_web_server_post_url = destination_web_server_post_url
        self.queue = queue
        self.debug = debug
        self.streams = streams
        self.clients = []
        self.devices = {}
        self.max_retries = max_seiscomp_connection_retries
        self.retry_delay = connection_retry_delay


    def send_post(self, data):
        try:
            requests.post(self.destination_web_server_post_url, json=data)
        except requests.exceptions.RequestException as e:
            print(f"Error sending signal: {e}")


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

            self.devices[device_id].add_one_channel_packet(trace)

            serialized_output_packet = self.devices[device_id].get_last_packet_if_completed_with_all_channels(serialize=True)
            print(serialized_output_packet)
            if serialized_output_packet is not None:
                print(f"Sending data...")
                self.send_post(serialized_output_packet)
        except Exception as e:
            print(f"Handle data exception: {e}")


    def create_clients(self):
        self.clients = []
        for network, station, selector in self.streams:
            client = create_client(self.server_address, on_data=self.handle_data)
            client.select_stream(network, station, selector)
            self.clients.append(client)

    def run_client(self, client):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                client.run()
                break
            except Exception as e:
                print(f"Failed to connect to SeedLink server: {e}")
                retry_count += 1
                if retry_count < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds... (Attempt {retry_count}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    print("Max retries reached. Exiting.")
                    return

    def run(self):
        self.create_clients()
        threads = []
        for client in self.clients:
            thread = threading.Thread(target=self.run_client, args=(client,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


if __name__ == "__main__":
    queue = multiprocessing.Queue()
    server_address = '192.168.0.105:18000'
    # server_address = '192.168.82.209:18000'
    streams = [
        # ('XX', '15', 'CXZ'),
        ('XX', '15', 'CX?'),
        # ('XX', '18', 'CX?'),
        # ('XX', '37', 'CX?'),
        # ('XX', '38', 'CX?'),
        # ('YY', '39', 'CYZ'),
        # Add more streams as needed
    ]


    buffer_duration = 0.5  # Example buffer duration in seconds
    max_retries = 1  # Maximum number of reconnection attempts
    retry_delay = 1  # Delay between reconnection attempts in seconds
    seiscomp_client = SeisCompClient(server_address=server_address,
                                     streams=streams,
                                     queue=queue,
                                     destination_web_server_post_url='http://127.0.0.1:5000/update_signal',
                                     max_seiscomp_connection_retries=5,
                                     connection_retry_delay=5,
                                     debug=False
                                     )

    seiscomp_client.start()




















'''
class SeisCompClient(multiprocessing.Process):
    def __init__(self, server_address, streams, buffer_duration, queue, max_retries=5, retry_delay=5, debug=False):
        """
        :param server_address: Address of the SeedLink server.
        :param streams: List of tuples, each containing (network, station, selector).
        :param buffer_duration: Duration of the buffer in seconds.
        :param queue: multiprocessing.Queue to pass the data.
        :param max_retries: Maximum number of reconnection attempts.
        :param retry_delay: Delay between reconnection attempts in seconds.
        """
        super().__init__()
        self.server_address = server_address
        self.streams = streams
        self.buffer_duration = buffer_duration
        self.queue = queue
        self.debug = debug

        self.buffers = {stream[:2]: {'CXE': np.array([]), 'CXN': np.array([]), 'CXZ': np.array([])} for stream in
                        streams}
        self.start_times = {stream[:2]: {'CXE': None, 'CXN': None, 'CXZ': None} for stream in streams}
        self.end_times = {stream[:2]: {'CXE': None, 'CXN': None, 'CXZ': None} for stream in streams}

        self.clients = []
        self.max_retries = max_retries
        self.retry_delay = retry_delay


    def handle_data(self, trace):
        """
        Handles incoming trace data.

        :param trace: An object of class obspy.core.trace.Trace.
        """

        if self.debug:
            print(f"trace : {trace.__dict__}")

        #print(trace)
        if not isinstance(trace, Trace):
            return

        stream_key = (trace.stats.network, trace.stats.station)  # , trace.stats.channel)
        stream_channel = trace.stats.channel


        if stream_key not in self.buffers:
            return

        if len(self.buffers[stream_key][stream_channel]) == 0:
            self.start_times[stream_key] = trace.stats.starttime

        self.buffers[stream_key][stream_channel] = np.concatenate(
            [self.buffers[stream_key][stream_channel], trace.data], axis=-1)
        # print(np.array(trace.data).shape, np.array(self.buffers[stream_key][stream_channel]).shape)
        end_time = trace.stats.endtime
        # If the total duration of the buffer exceeds the buffer_duration, transfer its contents to the queue

        if (end_time - self.start_times[stream_key]) >= self.buffer_duration:

            output_trace = []
            for CH in self.buffers[stream_key].keys():

                bfr = np.array(self.buffers[stream_key][CH])

                if len(output_trace) == 0:
                    output_trace.append(bfr)
                else:
                    if len(bfr) < len(output_trace[-1]):
                        output_trace = list(np.array(output_trace)[:, :len(bfr)])
                    else:
                        bfr = list(np.array(bfr)[:len(output_trace[-1])])

                    output_trace.append(bfr)

            trace_info = {
                'signal': np.array(output_trace),
                'start_time': self.start_times[stream_key],
                'end_time': end_time,
                'sampling_rate': trace.stats.sampling_rate,
                'station': trace.stats.station,
                'network': trace.stats.network
            }

            # print('-' * 20)
            # for k in trace_info.keys():
            #     print(f"{k}: {trace_info[k]}")
            # print('-' * 20)

            self.queue.put(trace_info)
            self.buffers[stream_key] = {'CXE': np.array([]), 'CXN': np.array([]),
                                        'CXZ': np.array([])}  # Stream()  # Clear the buffer
            self.start_times[stream_key] = None

    def create_clients(self):
        self.clients = []
        for network, station, selector in self.streams:
            client = create_client(self.server_address, on_data=self.handle_data)
            client.select_stream(network, station, selector)
            self.clients.append(client)

    def run_client(self, client):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                client.run()
                break
            except Exception as e:
                print(f"Failed to connect to SeedLink server: {e}")
                retry_count += 1
                if retry_count < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds... (Attempt {retry_count}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    print("Max retries reached. Exiting.")
                    return

    def run(self):
        self.create_clients()
        threads = []
        for client in self.clients:
            thread = threading.Thread(target=self.run_client, args=(client,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()



class DeviceClient_speeded(multiprocessing.Process):
    def __init__(self, in_queue):
        super().__init__()
        self.in_queue = in_queue
        self.time_to_send_full_buffer_milliseconds = 5000

        self.sample_rate = 500
        self.gps_lat = 0
        self.gps_lon = 0
        self.id = -1
        self.signal_buffer = np.zeros((3, 100))

        self.current_buffer_len = 100
        self.current_buffer_speed = 5

    def send_signal(self):
        output_signal = None
        if self.signal_buffer.shape[-1] < self.current_buffer_speed:
            output_signal = self.signal_buffer.copy().tolist()
            self.signal_buffer = np.zeros((3, 10))
        else:
            output_signal = (np.array(self.signal_buffer)[:,:self.current_buffer_speed]).tolist()
            self.signal_buffer = self.signal_buffer[:, self.current_buffer_speed:]


        data = {
            'device_id': self.id,
            'gps_lat': self.gps_lat,
            'gps_lon': self.gps_lon,
            'sample_rate': self.sample_rate,
            'signal_buffer': output_signal
        }

        try:
            requests.post('http://127.0.0.1:5000/update_signal', json=data)
        except requests.exceptions.RequestException as e:
            print(f"Error sending signal: {e}")


    def run(self):
        while True:
            if self.in_queue.empty() == False:
                data = self.in_queue.get()
                self.id = int(data['station'])
                self.sample_rate = data['sampling_rate']
                self.signal_buffer = np.concatenate((self.signal_buffer, np.array(data['signal'])), axis=-1)
                #print(self.signal_buffer.shape)

            if self.signal_buffer.shape[-1] <= 20 or self.id == -1:
                time.sleep(0.1)
            else:
                if self.signal_buffer.shape[-1] != self.current_buffer_len:
                    self.current_buffer_len = self.signal_buffer.shape[-1]
                    self.current_buffer_speed = int(self.signal_buffer.shape[-1] * self.sample_rate / self.time_to_send_full_buffer_milliseconds)
                self.send_signal()

                time.sleep(float(self.current_buffer_speed / self.time_to_send_full_buffer_milliseconds))

class DeviceClient:
    def __init__(self, device_id, gps_lat, gps_lon, sample_rate=500):
        self.device_id = device_id
        self.gps_lat = gps_lat
        self.gps_lon = gps_lon
        self.sample_rate = sample_rate
        self.signal_buffer = np.zeros((3, 100))

    def generate_signal(self):
        while True:
            new_signal = np.random.randn(3, 100)
            self.signal_buffer = new_signal
            self.send_signal()
            time.sleep(0.1)

    def send_signal(self, data=None):
        if data is None:
            data = {
                'device_id': self.device_id,
                'gps_lat': self.gps_lat,
                'gps_lon': self.gps_lon,
                'sample_rate': self.sample_rate,
                'signal_buffer': self.signal_buffer.tolist()
            }
        try:
            requests.post('http://127.0.0.1:5000/update_signal', json=data)
        except requests.exceptions.RequestException as e:
            print(f"Error sending signal: {e}")


    def start(self):
        threading.Thread(target=self.generate_signal, daemon=True).start()

# Example usage
if __name__ == '__main__':
    queue = multiprocessing.Queue()
    server_address = '192.168.0.105:18000'
    #server_address = '192.168.82.209:18000'
    streams = [
        # ('XX', '15', 'CXZ'),
        ('XX', '15', 'CX?'),
        # ('XX', '18', 'CX?'),
        # ('XX', '37', 'CX?'),
        # ('XX', '38', 'CX?'),
        # ('YY', '39', 'CYZ'),
        # Add more streams as needed
    ]
    buffer_duration = 0.5  # Example buffer duration in seconds
    max_retries = 1  # Maximum number of reconnection attempts
    retry_delay = 1  # Delay between reconnection attempts in seconds
    seiscomp_client = SeisCompClient(server_address, streams, buffer_duration, queue, max_retries, retry_delay, debug=True)

    seiscomp_client.start()

    data_sender = DeviceClient(15, 0, 0)

    # data_sender.start()

    # Process data from the queue in the main process
    while True:
        time.sleep(0.1)
        data = queue.get()
        # print('Received data batch:')
        # print(f"Station: {data['station']}")
        # print(f"Network: {data['network']}")
        # print(f"Signal: {data['signal'].shape}")
        # print(f"Start Time: {data['start_time']}")
        # print(f"End Time: {data['end_time']}")
        # print(f"Sampling Rate: {data['sampling_rate']}")
        # print()
        data = {
            'device_id': int(data['station']), #f"station_{data['network']}:{data['station']}",
            'gps_lat': 0,
            'gps_lon': 0,
            'sample_rate': data['sampling_rate'],
            'signal_buffer': data['signal'].tolist()
        }
        data_sender.send_signal(data)

        # plt.figure(figsize=(12, 6))
        # clr = ["blue", "green", "red"]
        # for i in range(0, 3):
        #     plt.subplot(311 + i)
        #     plt.plot(data["signal"][i], color=clr[i])
        # plt.savefig(f"__{data['station']}__.jpg")
        # plt.close()

'''