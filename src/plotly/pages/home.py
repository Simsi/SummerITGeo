from dash import html, dcc
import dash

HOME_LAYOUT = html.Main(
    html.P(
        "Welcome to the Seismic Activity Monitoring System. Please select a tab to continue."
    )
)

dash.register_page(__name__, "/", layout=HOME_LAYOUT)
