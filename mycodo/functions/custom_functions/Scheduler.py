# coding=utf-8
#
#  scheduler.py - control pump weekly schedule and amount
from ast import While
import time
import datetime

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config import SCHEDULE_WEEKS
from mycodo.databases.models import CustomController
from mycodo.databases.models import Recipes
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
    },
    {
        'id': 'reservoir_size',
        'type': 'float',
        'default_value': 0,
        'required': True,
        'constraints_pass': constraints_pass_positive_or_zero_value,
        'name': 'Reservoir Size',
        'phrase': 'Reservoir water amount in gallons'
    },  
]

FUNCTION_INFORMATION = {
    'function_name_unique': 'Scheduler',
    'function_name': 'Scheduler',
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
        self.start_datetime = datetime.datetime.now()
        self.end_datetime = datetime.datetime.now()
        self.current_datetime = datetime.datetime.now()
       
        self._spraydata = {}
        self.weeks = {}
        self.duration = None
        self.passed_days = None
        self.current_week = None
        self.current_amount = None
        
        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        # Set sprayed no False
        try:
            self._spraydata = self.get_custom_option("sprayed")
            if(self._spraydata is None):
                self.logger.info("_spraydata not available")
                for wk in range(1,SCHEDULE_WEEKS+1):
                    week_spray = {"week_{}".format(wk) : False}
                    self._spraydata.update(week_spray)
                self.set_custom_option("sprayed",self._spraydata) 
                self.logger.info("spraydata initialized")

        except Exception as ex:
            self.logger.debug("Error initializing sprayed weeks {}".format(ex))

        if not testing:
            self.initialize_variables()

    def initialize_variables(self):
        self.timestamp = time.time()
        try:
            current_recipe = db_retrieve_table_daemon(Recipes).filter(Recipes.current == True).first()
            self.start_datetime =  current_recipe.start_date
            self.end_datetime = current_recipe.end_date

        except Exception as ex:
             self.logger.error(str(ex))
 
        self.output_raise_channel = self.get_output_channel_from_channel_id(
            self.output_raise_channel_id)
        self.logger.info(
            "Scheduler controller started with options: "
            "Output Raise: {}, Output_Raise_Channel: {},"
            "Period: {},".format(
            self.output_raise_device_id,
            self.output_raise_channel,
            self.update_period,
            ))
        try:
            if(self.current_datetime >= self.start_datetime):
                self.passed_days = (self.current_datetime - self.start_datetime).days
                self.current_week = (self.passed_days//7)+1
                self.current_amount = eval("self.week_"+str(self.current_week))

                self.logger.info("Days passed : {} , Current Week : {} ,"
                "Amount : {} ,Sprayed : {}".format(
                    self.passed_days,self.current_week,
                    self.current_amount*self.reservoir_size,
                    self._spraydata["week_{}".format(self.current_week)]))
            else:
                self.remaining_seconds = (self.start_datetime - self.current_datetime).total_seconds()
                days = int(self.remaining_seconds // (24 * 3600))
                self.remaining_seconds = self.remaining_seconds % (24 * 3600)
                hours = int(self.remaining_seconds // 3600)
                self.remaining_seconds %= 3600
                minutes = int(self.remaining_seconds // 60)
                self.remaining_seconds %= 60
                seconds = int(self.remaining_seconds)

                self.logger.info("Starting in : {} days {} hours {} minutes {} Seconds"
                .format(days,hours,minutes,seconds))

        except Exception as ex:
             self.logger.info(str(ex))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.update_period

        self.current_datetime = datetime.datetime.now()
        if(self.current_datetime >= self.start_datetime and self.end_datetime >= self.current_datetime):

            if(self._spraydata is not None):
                if(self.output_raise_channel is not None):
                    output_raise_state = self.control.output_state(
                        self.output_raise_device_id, self.output_raise_channel)

                
                passed_days = (self.current_datetime - self.start_datetime).days
                current_week = (passed_days//7)+1
                current_amount = eval("self.week_"+str(current_week))

                # self.logger.info("Days passed : {} , Current Week : {} ,"
                # "Amount : {} ,Sprayed : {}".format(
                #     passed_days,current_week,
                #     current_amount*self.reservoir_size,
                #     self._spraydata["week_{}".format(current_week)]))
                
                if(self._spraydata["week_{}".format(current_week)] == False):
                    if(self.output_raise_channel is None):
                        self.logger.error("Cannot start controller: Check output channel(s).")
                        return

                    try:
                        if(current_amount > 0):
                            if(self.output_raise_channel == 0):
                                self.control.output_on(
                                    self.output_raise_device_id,
                                    output_channel=self.output_raise_channel,
                                    amount = current_amount*self.reservoir_size,
                                    output_type = 'vol')
                                
                                self._spraydata.update({"week_{}".format(current_week) : True})
                                self.set_custom_option("sprayed",self._spraydata) 
                                self.logger.info("Spray status updated {}".format(self._spraydata))

                        else:
                            self.logger.info("Pump {} could not be fired on".format(self.output_raise_device_id))

                    except Exception as ex:
                        self.logger.info("Error Raising Output {}".format(ex))
            else:
                # Set sprayed no False
                try:
                    self._spraydata = {}
                    for wk in range(1,SCHEDULE_WEEKS+1):
                        week_spray = {"week_{}".format(wk) : False}
                        self._spraydata.update(week_spray)
                    self.set_custom_option("sprayed",self._spraydata) 
                    self.logger.info("spraydata initialized")

                except Exception as ex:
                    self.logger.debug("Error initializing sprayed weeks {}".format(ex))
   
    def stop_function(self):
        self.control.output_off(
            self.output_raise_device_id, self.output_raise_channel)
  
