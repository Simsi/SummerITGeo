from dash import html, dcc, Input, Output, callback
import dash
import requests
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
import plotly.graph_objects as go

SENSORS_LAYOUT = html.Main(
    className="signal-monitor-main",
    children=[
        html.Div(
            className="config-block",
            children=[
                html.Label(
                    htmlFor="deviceSelect",
                    children="Select Device: ",
                ),
                DEVICE_SELECT := dcc.Dropdown(
                    id="deviceSelect",
                    options={},
                    value=None,
                ),
                DEVICE_SELECT_BTN := html.Button(
                    id="selectDeviceBtn",
                    children="Select Device",
                ),
                html.Div(
                    className="input-group",
                    children=[
                        html.Label(
                            htmlFor="lpf",
                            children="LPF: ",
                        ),
                        LFP := dcc.Input(id="lpf", type="number"),
                        html.Label(
                            htmlFor="hpf",
                            children="HPF: ",
                        ),
                        HPF := dcc.Input(id="hpf", type="number"),
                        html.Label(
                            htmlFor="threshold",
                            children="Threshold: ",
                        ),
                        THRESHOLD := dcc.Input(id="threshold", type="number"),
                    ],
                ),
                UPDATE_CONFIG_BTN := html.Button(id="updateConfigBtn", children="Update Configuration"),
            ],
        ),
        html.Div(
            className="signal-block",
            children=[
                SENSORS_PLOTS := dcc.Graph(
                    id="signal-graph",
                ),
            ]
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
        SPECTROGRAM_PLOT := dcc.Graph(
            className="signal-spectrogram-block",
        ),
        html.Div(
            className="metrics-block",
            children="Metrics block 1",
        ),
        html.Div(
            className="metrics-block",
            children="Metrics block 2",
        ),
        html.Div(
            className="metrics-block",
            children="Metrics block 3",
        ),
    ],
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
