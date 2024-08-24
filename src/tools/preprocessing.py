from Device import Device
from seedlink_client import DeviceBuffer
import numpy as np
from scipy import signal

class SignalProcessor:
    def __init__(self):
        """
        Класс для обработки сигналов из DeviceBuffer.
        """

    def apply_filter(self, data, hpf_freq, lpf_freq, sample_rate):
        """
        Применяет фильтрацию к данным.
        """
        sos = signal.butter(4, [hpf_freq, lpf_freq], btype='band', fs=sample_rate, output='sos')
        
        return signal.sosfilt(sos, data, axis=-1)

    def process_single_packet(self, packet_data, hpf_freq, lpf_freq, sample_rate):
        """
        Обрабатывает один пакет данных.
        """
        filtered_data = self.apply_filter(packet_data, hpf_freq, lpf_freq, sample_rate)
        processed_data = signal.detrend(filtered_data, axis=-1)
        
        return processed_data

    def process_all_packets_separately(self, device: Device, device_buffer: DeviceBuffer):
        """
        Обрабатывает все пакеты данных в deque отдельно.
        """
        for i, (seq, packet_data) in enumerate(device_buffer.deque):
            processed_data = self.process_single_packet(packet_data, device.hpf_freq, device.lpf_freq, device.sample_rate)
            device_buffer.deque[i] = (seq, processed_data)

        return device, device_buffer


    def process_all_data_together(self, device: Device, device_buffer: DeviceBuffer):
        """
        Обрабатывает все данные в буфере как один большой массив.
        """
        all_data = np.concatenate([packet_data for seq, packet_data in device_buffer.deque], axis=-1)
        filtered_data = self.apply_filter(all_data, device.hpf_freq, device.lpf_freq, device.sample_rate)
        processed_data = signal.detrend(filtered_data, axis=-1)

        start_idx = 0
        for i, (seq, packet_data) in enumerate(device_buffer.deque):
            end_idx = start_idx + packet_data.shape[-1]
            device_buffer.deque[i] = (seq, processed_data[:, start_idx:end_idx])
            start_idx = end_idx
        
        return device, device_buffer




