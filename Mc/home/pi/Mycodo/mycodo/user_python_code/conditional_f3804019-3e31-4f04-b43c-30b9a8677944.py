import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.controllers.base_conditional import AbstractConditional
from mycodo.mycodo_client import DaemonControl
control = DaemonControl(pyro_timeout=30.0)

class ConditionalRun(AbstractConditional):
    def __init__(self, logger, function_id, message):
        super(ConditionalRun, self).__init__(logger, function_id, message, timeout=30.0)

        self.logger = logger
        self.function_id = function_id
        self.variables = {}
        self.message = message
        self.running = True

    def conditional_code_run(self):
        bool_water_float = self.condition("4d833828-4b1e-499d-826a-abbd2444b531")
        if bool_water_float is not None:
            if bool_water_float == 1:
                self.message += "The water level is low. Add water.\n"
                self.run_action("6172c78b-7934-48b3-a8dc-6202814ebb1d", message=self.message)
            else:
                self.message += "Water level is ok!"
                self.run_action("b28ca30e-fa40-4328-b217-202af5441bbe", message=self.message)    
        else:
            self.message += "No water float measurement found!"
            self.run_action("b28ca30e-fa40-4328-b217-202af5441bbe", message=self.message)

    def function_status(self):
        # Example code to provide a return status for other controllers and widgets.
        status_dict = {
            'string_status': "This is the demo status of the conditional controller. "
                             "The controller has looped {} times".format(self.loop_count),
            'loop_count': self.loop_count,
            'error': []
        }
        return status_dict
