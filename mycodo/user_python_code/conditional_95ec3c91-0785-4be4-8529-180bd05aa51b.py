import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.controllers.base_conditional import AbstractConditional
from mycodo.mycodo_client import DaemonControl
control = DaemonControl(pyro_timeout=30)

class ConditionalRun(AbstractConditional):
    def __init__(self, logger, function_id, message):
        super(ConditionalRun, self).__init__(logger, function_id, message, timeout=30)

        self.logger = logger
        self.function_id = function_id
        self.variables = {}
        self.message = message
        self.running = True

    def conditional_code_run(self):

        # Example code for learning how to use a Conditional. See the manual for more information.

        self.logger.info("This INFO log entry will appear in the Daemon Log")
        self.logger.error("This ERROR log entry will appear in the Daemon Log")

        if not hasattr(self, "loop_count"):  # Initialize objects saved across executions
            self.loop_count = 1
        else:
            self.loop_count += 1

        # Replace "asdf1234" with a Condition ID
        measurement = self.condition("{asdf1234}") 
        self.logger.info("Check this measurement in the Daemon Log. The value is {val}".format(val=measurement))

        if measurement is not None:  # If a measurement exists
            self.message += "This message appears in email alerts and notes.\n"

            if measurement < 23:  # If the measurement is less than 23
                self.message += "Measurement is too Low! Measurement is {meas}\n".format(meas=measurement)
                self.run_all_actions(message=self.message)  # Run all actions sequentially

            elif measurement > 27:  # Else If the measurement is greater than 27
                self.message += "Measurement is too High! Measurement is {meas}\n".format(meas=measurement)
                # Replace "qwer5678" with an Action ID
                self.run_action("{qwer5678}", message=self.message)  # Run a single specific Action

    def function_status(self):

        # Example code to provide a return status for other controllers and widgets.
        status_dict = {
            'string_status': "This is the demo status of the conditional controller. "
                             "The controller has looped {} times".format(self.loop_count),
            'loop_count': self.loop_count,
            'error': []
        }
        return status_dict
