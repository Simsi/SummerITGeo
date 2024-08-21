import dash
from dash import html, dcc, Input, Output
from dash.exceptions import PreventUpdate
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.plotly.app import app
from src.plotly.sensors.markup import SENSORS_LAYOUT
from src.plotly import callbacks

if __name__ == "__main__":
    app.layout = SENSORS_LAYOUT
    app.run_server(debug=True)
