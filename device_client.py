import numpy as np
import requests
import time
import threading

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

if __name__ == '__main__':
    # Example usage
    client1 = DeviceClient(device_id=1, gps_lat=55.0415, gps_lon=82.9336)
    client2 = DeviceClient(device_id=2, gps_lat=55.0405, gps_lon=82.9356)
    # client3 = DeviceClient(device_id=3, gps_lat=55.0424, gps_lon=82.9391)
    # client4 = DeviceClient(device_id=4, gps_lat=55.0425, gps_lon=82.9156)
    # client5 = DeviceClient(device_id=5, gps_lat=55.0475, gps_lon=82.9346)
    # client6 = DeviceClient(device_id=6, gps_lat=55.0425, gps_lon=82.9351)

    client1.start()
    client2.start()
    # client3.start()
    # client4.start()
    # client5.start()
    # client6.start()

    # Keep the main thread running
    while True:
        time.sleep(1)
