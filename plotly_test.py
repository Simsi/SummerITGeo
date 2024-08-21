import dash
from dash import html, dcc, Input, Output
from dash.exceptions import PreventUpdate
import requests
import plotly.graph_objects as go
from plotly.tools import make_subplots

app = dash.Dash(__name__)

graph = dcc.Graph(
    id="graph",)
data_get_interval = dcc.Interval(
    id="data-get-interval",
    interval=200,
    n_intervals=0
)
data_update_interval = dcc.Interval(
    id="data-update-interval",
    interval=20,
    n_intervals=0,
    disabled=True,
)
storage = dcc.Store(
    id="storage",
    storage_type="memory")

app.layout = html.Div([
    storage,
    data_get_interval,
    data_update_interval,
    graph
])

@app.callback(
    Output(storage, "data"),
    Input(data_get_interval, "n_intervals"),
)
def on_data_update(n_intervals):
    resp = requests.get("http://127.0.0.1:8000/data")
    if resp.status_code == 200:
        return resp.json()
    else:
        raise PreventUpdate

@app.callback(
    Output(graph, "figure"),
    Input(storage, "data"),
)
def update_graph(data):
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
        
        
if __name__ == "__main__":
    app.run_server(debug=True)
