from obspy import Trace
import numpy as np
from collections import OrderedDict
import copy
from src.tools.SeedLinkTimeGroupedThreeChansPacket import SeedLinkTimeGroupedThreeChansPacket


class Device():
    def __init__(self, device_id: tuple = ("XX", "15"),
                 sample_rate: int = 500,
                 lpf_freq: int = 10,
                 hpf_freq: int = 1,
                 threshold: int = 2,
                 signal_packets_memory_len: int = 10,
                 signal_buffer_max_len: int = 3000
                 ):
        self.sample_rate = sample_rate
        self.device_id = device_id
        self.lpf_freq = lpf_freq
        self.hpf_freq = hpf_freq
        self.threshold = threshold
        self.gps_lat = 0
        self.gps_lot = 0
        self.signal_time_synchronized_packets = OrderedDict()  # dictof SeedLinkPacket
        self.signal_packets_memory_len = signal_packets_memory_len  # 10 last packets will be saved
        self.signal_buffer = np.zeros((3, 0))  # concatenated signals
        self.signal_buffer_max_len = signal_buffer_max_len  # max len of buffer

    def __init__(self, trace : Trace,
                 lpf_freq: int = 10,
                 hpf_freq: int = 1,
                 threshold: int = 2,
                 signal_packets_memory_len: int = 10,
                 signal_buffer_max_len: int = 3000
                 ):

        self.sample_rate = trace.stats.sampling_rate
        self.device_id = (trace.stats.network, trace.stats.station)
        self.lpf_freq = lpf_freq
        self.hpf_freq = hpf_freq
        self.threshold = threshold
        self.signal_time_synchronized_packets = OrderedDict()  # dictof (starttime, endtime): SeedLinkPacket
        self.signal_packets_memory_len = signal_packets_memory_len  # 10 last packets will be saved
        self.signal_buffer = np.zeros((3, 0))  # concatenated signals
        self.signal_buffer_max_len = signal_buffer_max_len  # max len of buffer


    def add_one_channel_packet(self, trace: Trace = None):
        try:
            channel = trace.stats.channel
            sampling_rate = trace.stats.sampling_rate
            station = trace.stats.station
            network = trace.stats.network
            signal = trace.data
            start_time = trace.stats.starttime
            end_time = trace.stats.endtime

            packet_time_id = (str(start_time), str(end_time))
            device_id = (network, str(station))

            if packet_time_id not in self.signal_time_synchronized_packets.keys():
                self.signal_time_synchronized_packets[packet_time_id] = SeedLinkTimeGroupedThreeChansPacket(
                    station_id=device_id,
                    start_end_time=packet_time_id,
                    sample_rate=sampling_rate,
                )

            self.signal_time_synchronized_packets[packet_time_id].update_from_new_trace(trace)
            #self.signal_time_synchronized_packets[packet_time_id].signal_dict[channel] = np.array(signal)

            #print(self.signal_time_synchronized_packets[packet_time_id].__dict__)

            # todo adding to signal_buffer

            # check all storages has correct size after adding packet
            if len(self.signal_time_synchronized_packets.keys()) > self.signal_packets_memory_len:
                # pop oldest packet
                self.signal_time_synchronized_packets.popitem(last=False)

            if self.signal_buffer.shape[-1] > self.signal_buffer_max_len:
                self.signal_buffer = self.signal_buffer[:, -self.signal_buffer_max_len:]

        except Exception as e:
            print(f"ADDING ONE CHAN: {e}")


    def get_last_packet(self):
        last_key = next(reversed(self.signal_time_synchronized_packets))
        return self.signal_time_synchronized_packets[last_key]


    def is_last_packet_completed_with_all_channels(self):
        return self.get_last_packet().is_not_empty_channels_in_dict()


    def get_last_packet(self):
        last_key = next(reversed(self.signal_time_synchronized_packets))
        return self.signal_time_synchronized_packets[last_key]


    def serialize_packet(self, packet: SeedLinkTimeGroupedThreeChansPacket):
        copy_packet = copy.deepcopy(packet)
        for key in copy_packet.signal_dict.keys():
            copy_packet.signal_dict[key] = list(map(int, copy_packet.signal_dict[key].tolist()))
        return copy_packet.__dict__

    def get_last_packet_if_completed_with_all_channels(self, serialize = False):
        if self.is_last_packet_completed_with_all_channels():
            if serialize:
                return self.serialize_packet(self.get_last_packet())

            return self.get_last_packet()
        return None
    
    def update_gps(self, packet):
        self.gps_lat = packet["gps_lat"]
        self.gps_lon = packet["gps_lon"]
