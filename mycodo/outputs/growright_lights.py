# coding=utf-8
#
# pump_atlas_ezo_pmp.py - Output for Atlas Scientific EZO Pump
#
import copy
import datetime
import threading
import os
from flask_babel import lazy_gettext
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'unitless',
        'unit': 'none'
    } 
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'growright_lights',
    'output_name': "{}: Growright Macroponics".format(lazy_gettext('Growlights')),
    'output_manufacturer': 'Biotechnica llc',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value','value','value'],

    'url_manufacturer': 'https://www.biotechnica.us/',
    'url_datasheet': 'https://www.biotechnica.us/',
    'url_product_purchase': 'https://www.biotechnica.us/',

    'message': 'Growlights have three colours and each colour can be set with specfic duty cycle value between 0 and 255'
               'rate can be specified. Their minimum flow rate is 0.5 ml/min and their maximum is 105 ml/min.',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'button_send_volume',
        'button_send_duration',
        'button_on',
        'button_off'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi==0.19.0')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x77'],
    'i2c_address_editable': True,
    'ftdi_location': '/dev/ttyUSB0',
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    
    'custom_channel_options': [
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state when Mycodo starts'
        },
         {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': 'Set the state when Mycodo shuts down'
        },

    ],
    'custom_actions': [
        {
            'id': 'Red_Led',
            'type': 'integer',
            'default_value': 30,
            'name': "Red Led Value",
            'phrase': 'The Color when turning on in Single Color Mode, RGB format (red, green, blue), 0 - 255 each.'
        },  
         {
            'id': 'Green_Led',
            'type': 'integer',
            'default_value': 30,
            'name': "Green Led Value",
            'phrase': 'The Color when turning on in Single Color Mode, RGB format (red, green, blue), 0 - 255 each.'
        },  
         {
            'id': 'White_Led',
            'type': 'integer',
            'default_value': 30,
            'name': "White Led Value",
            'phrase': 'The Color when turning on in Single Color Mode, RGB format (red, green, blue), 0 - 255 each.'
        }
        #,
        # {
        #     'type': 'message',
        #     'default_value': """The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address."""
        # },
        # {
        #     'id': 'new_i2c_address',
        #     'type': 'text',
        #     'default_value': '0x67',
        #     'name': lazy_gettext('New I2C Address'),
        #     'phrase': lazy_gettext('The new I2C to set the device to')
        # },
        # {
        #     'id': 'set_i2c_address',
        #     'type': 'button',
        #     'name': lazy_gettext('Set I2C Address')
        # }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.atlas_device = None
        self.currently_dispensing = False
        self.interface = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)
        
        self.LOG_TEST = '/var/log/log_test.txt'
        
    def setup_output(self):
        self.setup_output_variables(OUTPUT_INFORMATION)
        self.interface = self.output.interface
        self.atlas_device = setup_atlas_device(self.output)
        self.output_setup = True

    def record_pwm(self, red_pwm=0, green_pwm=0,white_pwm=0):
        measure_dict = copy.deepcopy(measurements_dict)
        if red_pwm:
            measure_dict[0]['value'] = red_pwm
        if green_pwm:
            measure_dict[1]['value'] = green_pwm
        if white_pwm:
            measure_dict[2]['value'] = white_pwm
        add_measurements_influxdb(self.unique_id, measure_dict)


    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        try:
            if state == 'on' and output_type == 'sec':
                write_cmd = 'RGW,{},{},{}'.format(200,200,200)
            
            elif state == 'off':
                self.currently_dispensing = False
                write_cmd = 'RGW,{},{},{}'.format(0,0,0)
             
            else:
                self.logger.error(
                    "Invalid parameters: State: {state}, Type: {ot}, Mode: {mod}, Amount: {amt}, Flow Rate: {fr}".format(
                        state=state,
                        ot=output_type,
                        mod=self.options_channels['flow_mode'][0],
                        amt=amount,
                        fr=self.options_channels['flow_rate'][0]))
                return
            self.atlas_device.atlas_write(write_cmd)


            with open(self.LOG_TEST, 'a') as f:
                data = "{} : Command Sent : Device : {}  Command :{}".format(datetime.datetime.utcnow(),self.output.unique_id,write_cmd)
                f.write("\r\n")
                f.write(data )
            self.logger.debug("EZO-PMP command: {}".format(write_cmd))

        except Exception as ex:
            self.logger.error(ex)

    def is_on(self, output_channel=None):
        if self.is_setup():
            device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == self.unique_id)
            for each_dev_meas in device_measurements:
                if each_dev_meas.unit == 'minute':
                    last_measurement = read_last_influxdb(
                        self.unique_id,
                        each_dev_meas.unit,
                        each_dev_meas.channel,
                        measure=each_dev_meas.measurement)
                    if last_measurement:
                        try:
                            datetime_ts = datetime.datetime.strptime(
                                last_measurement[0][:-7], '%Y-%m-%dT%H:%M:%S.%f')
                        except:
                            # Sometimes the original timestamp is in milliseconds
                            # instead of nanoseconds. Therefore, remove 3 less digits
                            # past the decimal and try again to parse.
                            datetime_ts = datetime.datetime.strptime(
                                last_measurement[0][:-4], '%Y-%m-%dT%H:%M:%S.%f')
                        minutes_on = last_measurement[1]
                        ts_pmp_off = datetime_ts + datetime.timedelta(minutes=minutes_on)
                        now = datetime.datetime.utcnow()
                        is_on = bool(now < ts_pmp_off)
                        if is_on:
                            return True
            return False

    def is_setup(self):
        if self.output_setup:
            return True
        return False

 