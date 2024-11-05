# coding=utf-8
import copy
import time

from flask_babel import lazy_gettext
from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'electrical_potential',
        'unit': 'V'
    },
    1: {
        'measurement': 'electrical_current',
        'unit': 'A'
    },
    2: {
        'measurement': 'power',
        'unit': 'W'
    },
    3: {
        'measurement': 'energy',
        'unit': 'kWh'
    },
    4: {
        'measurement': 'frequency',
        'unit': 'Hz'
    },
    5: {
        'measurement': 'power_factor',
        'unit': 'unitless'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'GROWRIGHT_POWER_METER',
    'input_manufacturer': 'Growright Macroponics',
    'input_name': 'GrowRight Power Meter',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Voltage/Current',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.google.com/',
    'url_datasheet': 'https://www.google.com',

    'options_enabled': [
        'measurements_select',
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'serial', 'pyserial==3.5'),
        ('pip-pypi', 'modbus_tk', 'modbus_tk==1.1.2')
    ],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyS0',
    'uart_baud_rate': 9600,

    'custom_options': [],
    'custom_actions': []
}

class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor ElectricalConductivity"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.serial = None
        # Initialize custom options
        self.serial_device = None
        self.interface = None
        self.sensor = None
        self.cst = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        self.interface = self.input_dev.interface

        import serial
        import modbus_tk
        from modbus_tk import modbus_rtu
        import modbus_tk.defines as cst

        self.cst = cst
        self.serial_device = serial.Serial(
                               port='/dev/ttyS0',
                               baudrate=9600,
                               bytesize=8,
                               parity='N',
                               stopbits=1,
                               xonxoff=0
                              )
        self.sensor = modbus_rtu.RtuMaster(self.serial_device)
        self.sensor.set_timeout(2.0)
        self.sensor.set_verbose(True)


    def get_measurement(self):
        """ Gets the sensor's measurement """
        self.return_dict = copy.deepcopy(measurements_dict)
        data = self.sensor.execute(1, self.cst.READ_INPUT_REGISTERS, 0, 10)
        
        if self.is_enabled(0):
            voltage = data[0] / 10.0
            self.value_set(0, voltage)
        else:
            self.logger.exception("voltage not enabled")

        if self.is_enabled(1):
            current = (data[1] + (data[2] << 16)) / 1000.0 
            self.value_set(1,current)

        if self.is_enabled(2):
            power = (data[3] + (data[4] << 16)) / 10.0
            self.value_set(2,power)

        if self.is_enabled(3):
            energy = data[5] + (data[6] << 16)
            self.value_set(3,energy)

        if self.is_enabled(4):
            frequency = data[7] / 10.0
            self.value_set(4,frequency)

        if self.is_enabled(5):
            power_factor = data[8] / 100.0
            self.value_set(5,power_factor)

        # if self.is_enabled(6):
        #     alarm = data[9]
        #     self.value_set(6,alarm)

        return self.return_dict

