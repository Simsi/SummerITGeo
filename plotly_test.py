import plotly.express as px
import requests
import time

server_addr = "http://127.0.0.1:5000"
current_sequence = 0
fig = px.line(y=[0, 0, 0])
fig.show()
while True:
    response = requests.get(f"http://127.0.0.1:5000/data")
    if response.status_code == 200:
        data = response.json()
        for seq, data in data:
            if seq > current_sequence:
                current_sequence = seq
                data = [
                    data["signal_dict"]["CXE"],
                    data["signal_dict"]["CXN"],
                    data["signal_dict"]["CXZ"],
                ]
                print(data)
                fig.data[0].y = data[0]
                time.sleep(0.4)
                

