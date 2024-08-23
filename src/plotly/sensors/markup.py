from dash import html, dcc, Input, Output

SENSORS_LAYOUT = html.Div([
    SENSORS_PLOTS := dcc.Graph(
        id="graph",
    ),
    DATA_GET_INTERVAL := dcc.Interval(
        id="data-get-interval",
        interval=200,
        n_intervals=0
    ),
    DATA_UPDATE_INTERVAL := dcc.Interval(
        id="data-update-interval",
        interval=20,
        n_intervals=0,
        disabled=True,
    ),
    SENSORS_BUFFER_STORE := dcc.Store(
        id="storage",
        storage_type="memory"
    )
])
