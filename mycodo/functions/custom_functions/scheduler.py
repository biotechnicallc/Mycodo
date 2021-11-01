# coding=utf-8
#
#  scheduler.py - control pump weekly schedule and amount
import time
import datetime

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


FUNCTION_INFORMATION = {
    'function_name_unique': 'Scheduler',
    'function_name': 'Scheduler',
    'message': 'A Controller to control weekly schedule of Pump.',

    'options_enabled': [],

    'custom_options': [
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
        },
         {
            'id': 'week_1',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 1',
            'phrase': 'Week 1 Amount'
        },
       {
            'id': 'week_2',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 2',
            'phrase': 'Week 2 Amount'
        },
        {
            'id': 'week_3',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 3',
            'phrase': 'Week 3 Amount'
        },
        {
            'id': 'week_4',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 4',
            'phrase': 'Week 4 Amount'
        },
        {
            'id': 'week_5',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 5',
            'phrase': 'Week 5 Amount'
        },
        {
            'id': 'week_6',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 6',
            'phrase': 'Week 6 Amount'
        },
        {
            'id': 'week_7',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 7',
            'phrase': 'Week 7 Amount'
        },
        {
            'id': 'week_8',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Week 8',
            'phrase': 'Week 8 Amount'
        }
    ]
}


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
        self.week_1 = None
        self.week_2 = None
        self.week_3 = None
        self.week_4 = None
        self.week_5 = None
        self.week_6 = None
        self.week_7 = None
        self.week_8 = None

        self.duration = None
        self.sprayed = [False,False,False,False,False,False,False,False]
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
            "Period: {},"
            "Week_1: {}, Week_2: {},"
            "Week_3: {}, Week_4: {},"
            "Week_5: {}, Week_6: {},"
            "Week_7: {}, Week_8: {}".format(
                self.output_raise_device_id,
                self.output_raise_channel,
                self.update_period,
                self.week_1,
                self.week_2,
                self.week_3,
                self.week_4,
                self.week_5,
                self.week_6,
                self.week_7,
                self.week_8))

        self.amounts =  [self.week_1,self.week_2,
                        self.week_3,self.week_4,
                        self.week_5,self.week_6,
                        self.week_7,self.week_8]
       
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
  
