# coding=utf-8
#
#  scheduler.py - control pump weekly schedule and amount
import time
import datetime

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config import SCHEDULE_WEEKS
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

custom_ = [
    {
        'id': 'output_raise',
        'type': 'select_measurement_channel',
        'default_value': '',
        'required': True,
        'options_select': [
            'Output_Channels_Measurements',
        ],
        'name': 'Output (Raise)',
        'phrase': 'Select an output to control that will raise the measurement'
    },
    {
        'id': 'update_period',
        'type': 'float',
        'default_value': 5,
        'required': True,
        'constraints_pass': constraints_pass_positive_value,
        'name': lazy_gettext('Period (seconds)'),
        'phrase': lazy_gettext('The duration (seconds) between measurements or actions')
    }  
]

FUNCTION_INFORMATION = {
    'function_name_unique': 'Multipoint',
    'function_name': 'Multipoint',
    'message': 'A Controller to control weekly schedule of Pump.',
    'options_enabled': [],
    'custom_options': custom_
}

weeks_option = []
for wk in range(1,SCHEDULE_WEEKS+1):
    week_ = {
        'id': 'week_{}'.format(wk),
        'type': 'integer',
        'default_value': 0,
        'required': True,
        'constraints_pass': constraints_pass_positive_or_zero_value,
        'name': 'Week {}'.format(wk),
        'phrase': 'Week {} Amount'.format(wk)
    }
    weeks_option.append(week_)
FUNCTION_INFORMATION['custom_options'].extend(weeks_option)

class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super(CustomModule, self).__init__(function, testing=testing, name=__name__)
        self.control_variable = None
        self.timestamp = None
        self.control = DaemonControl()
        self.timer_loop = time.time()

        # Initialize custom options
        self.output_raise_measurement_id = None
        self.output_raise_channel_id = None
        self.output_raise_channel = None
        self.update_period = None
        self.amounts = []
        for wk in range(0,SCHEDULE_WEEKS):
            self.amounts[wk] = None
        
        self.duration = None
        self.sprayed = []
        for wk in range(0,SCHEDULE_WEEKS):
            self.sprayed[wk] = None

        self.weeks = []
        self.start_datetime = datetime.datetime.now().date()
        self.current_datetime = datetime.datetime.now().date()
        
         # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.initialize_variables()

    def initialize_variables(self):
        self.timestamp = time.time()

        self.output_raise_channel = self.get_output_channel_from_channel_id(
            self.output_raise_channel_id)
        self.logger.info(
            "Scheduler controller started with options: "
            "Output Raise: {}, Output_Raise_Channel: {},"
            "Period: {},".format(
            self.output_raise_device_id,
            self.output_raise_channel,
            self.update_period
            ))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.update_period

        output_raise_state = self.control.output_state(
            self.output_raise_device_id, self.output_raise_channel)

        self.current_datetime = datetime.datetime.now().date()
        passed_days = abs(self.start_datetime - self.current_datetime).days
        current_week = passed_days//7
        self.logger.info("Days passed : {} , Weeks passed : {} ,"
        "Amount : {} ,Sprayed : {}".format(
            passed_days,current_week,
            self.amounts[current_week],
            self.sprayed[current_week]))

        if(self.sprayed[current_week] == False):
            if (self.output_raise_channel is None):
                self.logger.error("Cannot start controller: Check output channel(s).")
                return
           
            if(self.amounts[current_week] > 0):
                if(self.output_raise_channel == 0):
                    self.control.output_on(
                        self.output_raise_device_id,
                        output_channel=self.output_raise_channel,
                        amount = self.amounts[current_week],
                        output_type = 'vol')

                else:
                    self.control.output_on(
                        self.output_raise_device_id,
                        output_channel=self.output_raise_channel,
                        amount = self.amounts[current_week],
                        output_type = 'sec')

            if(output_raise_state == 'on'):
                self.sprayed[current_week] = True
                self.logger.info("Spray status set to true")

            else:
                self.logger.info("Pump could not be fired on")

    def stop_function(self):
        self.control.output_off(
            self.output_raise_device_id, self.output_raise_channel)
  
