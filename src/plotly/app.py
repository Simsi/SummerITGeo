import dash
from pathlib import Path
from dash import html, dcc, Input, Output, callback
from dash.exceptions import PreventUpdate
import requests

pages_folder = Path(__file__).parent / "pages"

app = dash.Dash(
    __name__, use_pages=True, pages_folder=pages_folder, prevent_initial_callbacks=True
)

app.layout = [
    html.Header(
        [
            html.Div(
                "LOGO",
                id="logo",
            ),
            html.H1("Seismic Activity Monitoring"),
            STATUS_UPDATE_INTERVAL := dcc.Interval("status_update_interval", interval=1000),
            STATUS_STORE := dcc.Store("status_store", storage_type="memory"),
        ]
    ),
    html.Nav(
        [
            dcc.Link(f"{page['name']}", href=page["relative_path"])
            for page in dash.page_registry.values()
        ]
    ),
    dash.page_container,
]

@callback(Output("status_store", "data"), Input("status_update_interval", "n_intervals"))
def update_status(_):
    resp = requests.get("http://127.0.0.1:8000/status")
    if resp.status_code == 200:
        jsoned = resp.json()
        print(jsoned)
        return jsoned
    else:
        raise PreventUpdate
