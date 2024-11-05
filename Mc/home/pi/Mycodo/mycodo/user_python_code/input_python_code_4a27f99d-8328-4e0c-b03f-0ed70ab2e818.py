import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.influx import add_measurements_influxdb
control = DaemonControl()

class PythonInputRun:
    def __init__(self, logger, input_id, measurement_info):
        self.logger = logger
        self.input_id = input_id
        self.measurement_info = measurement_info

    def store_measurement(self, channel=None, measurement=None, timestamp=None):
        if None in [channel, measurement]:
            return
        measure = {channel: {}}
        measure[channel]['measurement'] = self.measurement_info[channel]['measurement']
        measure[channel]['unit'] = self.measurement_info[channel]['unit']
        measure[channel]['value'] = measurement
        if timestamp:
            measure[channel]['timestamp_utc'] = timestamp
        add_measurements_influxdb(self.input_id, measure)

    def python_code_run(self):
        import random  # Import any external libraries

        # Get measurements/values (for example, these are randomly-generated numbers)
        random_value_channel_0 = 0

        # Store measurements in database (must specify the channel and measurement)
        self.store_measurement(channel=0, measurement=random_value_channel_0)
