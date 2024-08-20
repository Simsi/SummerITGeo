
from classes import SeedLinkTimeGroupedThreeChansPacket


import eventlet
eventlet.monkey_patch()  # This should be the first import

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import numpy as np
import threading
import multiprocessing
import time
from scipy import signal

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

thread = None
devices = {}

class Device:
    def __init__(self, device_id, gps_lat, gps_lon, sample_rate=500, lpf=10, hpf=1, threshold=2, buffer_length=2000):
        self.device_id = device_id
        self.gps_lat = gps_lat
        self.gps_lon = gps_lon
        self.sample_rate = sample_rate
        self.lpf = lpf
        self.hpf = hpf
        self.threshold = threshold
        self.device_buffer = np.zeros((3, buffer_length))
        self.buffer_length = buffer_length
        self.lock = threading.Lock()

    def update_signal(self, new_signal):
        filtered = []
        lpf = signal.butter(N=4, Wn=self.lpf, btype='low', analog=False, output='sos', fs=self.sample_rate)
        hpf = signal.butter(N=4, Wn=self.hpf, btype='high', analog=False, output='sos', fs=self.sample_rate)

        for chan in new_signal:

            fltrd = signal.sosfilt(lpf, chan)
            fltrd = signal.sosfilt(hpf, fltrd)
            filtered.append(fltrd)


        new_signal = np.array(filtered)

        with self.lock:
            self.device_buffer = np.roll(self.device_buffer, -new_signal.shape[1], axis=1)
            self.device_buffer[:, -new_signal.shape[1]:] = new_signal

    def to_dict(self):
        return {
            'device_id': self.device_id,
            'gps_lat': self.gps_lat,
            'gps_lon': self.gps_lon,
            'sample_rate': self.sample_rate,
            'lpf': self.lpf,
            'hpf': self.hpf,
            'threshold': self.threshold,
            'status': 'CONNECTED',  # You can customize this status
            'last_event_time': 'N/A',  # Customize as needed
            'lon': self.gps_lon,
            'lat': self.gps_lat
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signal_monitor')
def signal_monitor():
    return render_template('signal_monitor.html', devices=devices.values())

@app.route('/map')
def map_view():
    devices_dict = [device.to_dict() for device in devices.values()]
    return render_template('map.html', devices=devices_dict)

@app.route('/system_settings')
def system_settings():
    return render_template('system_settings.html')

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.json

    packet = SeedLinkTimeGroupedThreeChansPacket(**data)
    #print(packet.__dict__)

    (network, device_id) = packet.station_id
    gps_lat = packet.gps_lat
    gps_lon = packet.gps_lon
    sample_rate = packet.sample_rate

    signal_buffer = packet.get_buffer_if_all_chans_got()

    if device_id not in devices.keys():
        devices[device_id] = Device(device_id, gps_lat, gps_lon, sample_rate)

    #signal_buffer = signal.decimate(signal_buffer, 5)
    devices[device_id].update_signal(signal_buffer)
    return jsonify({'status': 'success'})

@socketio.on('update_device_config')
def handle_update_device_config(data):
    device_id, lpf, hpf, threshold = data['device_id'], int(data['lpf']), int(data['hpf']), int(data['threshold'])
    devices[device_id].lpf = lpf
    devices[device_id].hpf = hpf
    devices[device_id].threshold = threshold
    #socketio.emit()



@socketio.on('select_device')
def handle_select_device(data):
    global thread
    device_id = data['device_id']
    device = devices.get(device_id)
    print(device)
    try:
        thread.terminate()
        thread = None
    except:
        pass

    thread = multiprocessing.Process(target=send_dev_signal, args=(device,))
    # thread.run()

    if device:
        response = {
            'lpf': device.lpf,
            'hpf': device.hpf,
            'threshold': device.threshold,
        }
        socketio.emit('device_config', response)
    thread.run()


def send_dev_signal(device):
    print(device.device_id)
    while True:
        with device.lock:

            signal_data = device.device_buffer
            signal_data = signal.detrend(signal_data, axis=0)
            signal_data = signal_data / np.max(signal_data, axis=1, keepdims=True)

            signal_data = signal_data.tolist()
            print(np.array(signal_data).shape)
        socketio.emit('realtime_signal', {'device_id': int(device.device_id), 'signal': signal_data})
        time.sleep(0.05)



if __name__ == '__main__':
    socketio.run(app, debug=True)
