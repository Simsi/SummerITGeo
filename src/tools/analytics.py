from Device import Device
from seedlink_client import DeviceBuffer

class Analytics:
    """Parent class to all analytics."""
    def __init__(self, return_name: str):
        pass

    def run_analytics(self, device: Device, device_buffer: DeviceBuffer) -> tuple[str, ]:
        """
        Interface method.
        Child classes run designated analyses and return name and result value.
        """

class ThresholdAnalytics(Analytics):
    """Finds out whether a signal in bufffer is above a threshold."""
    def __init__(self, return_name: str = "threshold_overflow"):
        self.return_name = return_name

    def run_analytics(self, device: Device, device_buffer: DeviceBuffer) -> tuple[str, ]:
        #overflow_state: bool = False       # not used
        threshold: int = device.threshold

        #can be implemented as abs max w/ numpy list
        for _, buffer_data_element in device_buffer.deque:
            #buffer_data_element is a jsonified SeedLinkTimeGroupedThreeChansPacket
            for _, chanel_data in buffer_data_element["signal_dict"]:
                for value in chanel_data:
                    if value > threshold:
                        return self.return_name, True #overflow_state
        return self.return_name, False #overflow_state



class AnalyticsAgent:
    """
    Collects types of analytics as child classes and runs them.
    Outputs a dictionary of analytics results, ready to be jsonified.
    """
    def __init__(self):
        self.analytics_list: list[Analytics] = []

    def add_analytics(self, analytics: Analytics) -> None:
        """Adds analytics classes to the list of analytics to be processed."""
        self.analytics_list.append(analytics)

    # if i get device params w/o copying itself, this could speed us up
    def run_analytics(self, device: Device, device_buffer: DeviceBuffer) -> dict[str, ]:
        """Runs all analytics in the list, updatng dictionary of results."""
        ret: dict[str, ] = {}
        for analytics in self.analytics_list:
            analytics_name, analytics_result = analytics.run_analytics(device, device_buffer)
            ret[analytics_name] = analytics_result
        return ret
