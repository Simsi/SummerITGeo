import plotly.express as px
import requests

server_addr = "http://127.0.0.1:5000"
current_sequence = 0
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
                fig = px.line(y=data)
                fig.show()
                


