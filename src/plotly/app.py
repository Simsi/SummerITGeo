import dash
from pathlib import Path
from dash import html, dcc

pages_folder = Path(__file__).parent / "pages"

app = dash.Dash(
    __name__, use_pages=True, pages_folder=pages_folder, prevent_initial_callbacks=True
)

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    dcc.Link(
                        f"{page['name']} - {page['path']}", href=page["relative_path"]
                    )
                )
                for page in dash.page_registry.values()
            ]
        ),
        dash.page_container,
    ]
)
