import dash
from pathlib import Path
from dash import html, dcc

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
        ]
    ),
    html.Nav(
        [
            dcc.Link(
                f"{page['name']}", href=page["relative_path"]
            )
            for page in dash.page_registry.values()
        ]
    ),
    dash.page_container,
]
