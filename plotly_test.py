from src.plotly.app import app
from src.plotly.sensors.markup import SENSORS_LAYOUT
# do not delete! callbacks import
from src.plotly import callbacks

if __name__ == "__main__":
    app.layout = SENSORS_LAYOUT
    app.run_server(debug=True)
