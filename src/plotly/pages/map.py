from dash import html, dcc, Input, Output, callback
import dash
import requests
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import dash_leaflet as dl

MAP_LAYOUT = html.Main(
    className="map-main",
    children=[
        html.Table(
            id="deviceTable",
            className="deviceTable",
            children=[
                html.Thead(
                    children=[
                        html.Tr(
                            children=[
                                html.Th(
                                    children="ID",
                                ),
                                html.Th(
                                    children="Status",
                                ),
                                html.Th(
                                    children="Last event time",
                                ),
                                html.Th(
                                    children="Threshold",
                                ),
                                html.Th(
                                    children="Lon",
                                ),
                                html.Th(
                                    children="Lat",
                                ),
                            ]
                        )
                    ]
                ),
                DEVICES_ITEMS := html.Tbody(),
            ],
        ),
        MAP := dl.Map(
            dl.TileLayer(),
            center=[0, 0],
            zoom=6,
            id="map",
            className="system-map",
        ),
        html.Div(
            className="event-logs",
            children=html.Table(
                children=[
                    html.Thead(
                        children=html.Tr(
                            children=[
                                html.Th(
                                    children="Event ID",
                                ),
                                html.Th(
                                    children="Devices",
                                ),
                                html.Th(
                                    children="Start time",
                                ),
                                html.Th(
                                    children="End time",
                                ),
                                html.Th(
                                    children="Description",
                                ),
                            ]
                        )
                    ),
                    EVENT_LOGS := html.Tbody(),
                ]
            ),
        ),
        html.Div(
            className="metrics-map-block",
            children="Metrics map block 1",
        ),
        html.Div(
            className="metrics-map-block",
            children="Metrics map block 2",
        ),
    ],
)


@callback(
    Output(MAP, "children"),
    Input("status_store", "data"),
)
def update_map(data):
    items = [dl.TileLayer()]
    for device_id, device in data.items():
        gps_lat = device["gps_lat"]
        gps_lon = device["gps_lon"]
        threshold_overflow = device["threshold_overflow"]
        items.append(
            dl.Marker(
                position=[gps_lat, gps_lon],
                children=dl.Tooltip(
                    f"device: {device_id}",
                ),
            )
        )
        if threshold_overflow:
            items.append(
                dl.Circle(
                    center=[gps_lat, gps_lon],
                    # in meters
                    radius=1000,
                    color="red",
                )
            )
    return items


dash.register_page(__name__, "/map", layout=MAP_LAYOUT)
