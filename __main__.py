from plotly_test import app
from multiprocessing import Process
from seedlink_client import start_client


if __name__ == "__main__":
    Process(target=start_client).start()

    app.run_server(debug=True)
