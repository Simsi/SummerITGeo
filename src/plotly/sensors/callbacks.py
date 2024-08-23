from dash import Input, Output
from dash.exceptions import PreventUpdate
from src.plotly.app import app
import requests
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from .markup import SENSORS_PLOTS, SENSORS_BUFFER_STORE, DATA_GET_INTERVAL, DATA_UPDATE_INTERVAL


@app.callback(
    Output(SENSORS_BUFFER_STORE, "data"),
    Input(DATA_GET_INTERVAL, "n_intervals"),
)
def on_data_update(n_intervals):
    """updates site upon recievng data package"""
    resp = requests.get("http://127.0.0.1:8000/data")
    if resp.status_code == 200:
        return resp.json()
    else:
        raise PreventUpdate

@app.callback(
    Output(SENSORS_PLOTS, "figure"),
    Input(SENSORS_BUFFER_STORE, "data"),
)
def update_graph(data):
    """updates graph"""
    seq: int
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
    ys = [[], [], []]
    total_len = 0
    for seq, payload in data:
        signal_dict = payload["signal_dict"]
        for y, ny in zip(ys, [signal_dict["CXE"], signal_dict["CXN"], signal_dict["CXZ"]]):
            total_len += len(ny)
            y.extend(ny)
    x = tuple(range(total_len // 3))
    for i, y in enumerate(ys):
        fig.append_trace(
            go.Scatter(x=x, y=y, name="E", mode="lines"), row=i + 1, col=1
        )
    return fig
