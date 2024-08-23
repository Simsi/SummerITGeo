from dash import html, dcc, Input, Output, State, callback
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
                UPDATE_DEVICES_BTN := html.Button(
                    id="selectDeviceBtn",
                    children="Update device list",
                ),
                DEVICE_SELECT := dcc.Dropdown(
                    id="deviceSelect",
                    options={},
                    value=None,
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
                UPDATE_CONFIG_BTN := html.Button(
                    id="updateConfigBtn", children="Update config"
                ),
            ],
        ),
        html.Div(
            className="signal-block",
            children=[
                SENSORS_PLOTS := dcc.Graph(
                    id="signal-graph",
                ),
            ],
        ),
        DATA_GET_INTERVAL := dcc.Interval(
            id="data-get-interval", interval=200, n_intervals=0, disabled=True
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
    State(DEVICE_SELECT, "value"),
    prevent_initial_call=True,
)
def on_data_update(n_intervals, device_network_station_id: str):
    resp = requests.get(f"http://127.0.0.1:8000/data/{device_network_station_id}")
    if resp.status_code == 200:
        return resp.json()
    else:
        raise PreventUpdate


@callback(
    Output(DEVICE_SELECT, "options"),
    Input(UPDATE_DEVICES_BTN, "n_clicks"),
    prevent_initial_call=False,
)
def update_devices(n_clicks):
    resp = requests.get("http://127.0.0.1:8000/devices")
    device_options = {}
    jsoned = resp.json()
    for network, station_id in jsoned:
        device_options[f"{network}/{station_id}"] = f"device {network} - {station_id}"
    if resp.status_code == 200:
        return device_options
    else:
        raise PreventUpdate


@callback(
    Output(DATA_GET_INTERVAL, "disabled"),
    Input(DEVICE_SELECT, "value"),
    prevent_initial_call=True,
)
def on_device_selection(device_network_station_id):
    return False


@callback(
    Output(SENSORS_PLOTS, "figure"),
    Input(SENSORS_BUFFER_STORE, "data"),
    prevent_initial_call=True,
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
    for i, (y, name) in enumerate(zip(ys, ["CXE", "CXN", "CXZ"])):
        fig.append_trace(
            go.Scatter(x=x, y=y, name=name, mode="lines"), row=i + 1, col=1
        )
    return fig


dash.register_page(__name__, "/sensors", layout=SENSORS_LAYOUT)
