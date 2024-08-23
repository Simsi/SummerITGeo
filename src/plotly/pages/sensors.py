from dash import html, dcc, Input, Output, callback
import dash
import requests
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
import plotly.graph_objects as go

SENSORS_LAYOUT = html.Div(
    [
        SENSORS_PLOTS := dcc.Graph(
            id="graph",
        ),
        DATA_GET_INTERVAL := dcc.Interval(
            id="data-get-interval", interval=200, n_intervals=0
        ),
        DATA_UPDATE_INTERVAL := dcc.Interval(
            id="data-update-interval",
            interval=20,
            n_intervals=0,
            disabled=True,
        ),
        SENSORS_BUFFER_STORE := dcc.Store(id="storage", storage_type="memory"),
    ]
)


@callback(
    Output(SENSORS_BUFFER_STORE, "data"),
    Input(DATA_GET_INTERVAL, "n_intervals"),
)
def on_data_update(n_intervals):
    resp = requests.get("http://127.0.0.1:8000/data")
    if resp.status_code == 200:
        return resp.json()
    else:
        raise PreventUpdate


@callback(
    Output(SENSORS_PLOTS, "figure"),
    Input(SENSORS_BUFFER_STORE, "data"),
)
def update_graph(data):
    seq: int
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
    ys = [[], [], []]
    total_len = 0
    for seq, payload in data:
        signal_dict = payload["signal_dict"]
        for y, ny in zip(
            ys, [signal_dict["CXE"], signal_dict["CXN"], signal_dict["CXZ"]]
        ):
            total_len += len(ny)
            y.extend(ny)
    x = tuple(range(total_len // 3))
    for i, y in enumerate(ys):
        fig.append_trace(go.Scatter(x=x, y=y, name="E", mode="lines"), row=i + 1, col=1)
    return fig


dash.register_page(__name__, "/sensors", layout=SENSORS_LAYOUT)
