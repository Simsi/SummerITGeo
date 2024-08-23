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
    """
    Callback function that updates the data in the SENSORS_BUFFER_STORE component.

    Parameters:
        n_intervals (int): The number of intervals that have elapsed since the last update.
        device_network_station_id (str): The selected device network and station ID.

    Returns:
        dict: The JSON response from the HTTP request to the server into the DATA_GET_INTERVAL component.

    Raises:
        PreventUpdate: If the HTTP request returns a status code other than 200.

    This function is triggered when the DATA_GET_INTERVAL component's n_intervals property changes, which occurs every 200 milliseconds.
    It makes a GET request to the server at http://127.0.0.1:8000/data/{device_network_station_id} which is http://127.0.0.1:8000/data/{network}/{device_id}
    and returns the JSON response if the request is successful (status code 200).
    Otherwise, it raises a PreventUpdate exception to prevent the component from updating.
    """
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
    """
    Updates the options for the DEVICE_SELECT component by doing a GET request to http://127.0.0.1:8000/devices.

    Parameters:
        n_clicks (int): The number of clicks on the UPDATE_DEVICES_BTN component.

    Returns:
        dict: A dictionary of device options where the keys are the device network and station IDs(in format "{network}/{station_id}" for simplicity), and the values are the corresponding device names.

    Raises:
        PreventUpdate: If the HTTP request to retrieve the device options fails. Which does nothing.
    """
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
    """
    Callback function that updates the disabled status of the DATA_GET_INTERVAL component.

    Parameters:
        device_network_station_id (Any): The selected device network and station ID.

    Returns:
        bool: False to enable the DATA_GET_INTERVAL component.

    This function is triggered when the DEVICE_SELECT component's value property changes.
    It returns False to enable the DATA_GET_INTERVAL component.
    """
    return False


@callback(
    Output(SENSORS_PLOTS, "figure"),
    Input(SENSORS_BUFFER_STORE, "data"),
    prevent_initial_call=True,
)
def update_graph(data):
    """
    Updates the figure of the SENSORS_PLOTS component based on the data stored in the SENSORS_BUFFER_STORE.

    Parameters:
        data (Any): The data stored in the SENSORS_BUFFER_STORE, containing a sequence of payloads with signal dictionaries.

    Returns:
        fig (plotly.graph_objects.Figure): The updated figure object to be displayed in the SENSORS_PLOTS component.
    """
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
