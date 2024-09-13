import os 
import logging
import subprocess
import time
from config import BOOT_PATH

class CloudFlareConfig:
    def __init__(self):
        self.logger = logging.getLogger('mycodo.daemon')
        self.logger.setLevel(logging.INFO)

        self.period_timer = time.time()
        self.ap_enabled = False
        self.config_file = os.path.join(BOOT_PATH, 'cloudflare.config')
        

    def is_config_file(self):
        if os.path.isfile(self.config_file):
            return True
        else:
            return False
    
    def run_config(self):
        if self.is_config_file():
            # Read the file content
            with open(self.config_file, 'r') as file:
                commands = file.read()
            # Execute the commands
            try:
                result = subprocess.run(commands, shell=True, check=True, text=True, capture_output=True)
                os.remove(self.config_file)
                return result.stdout
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")  
                return e.stderr
    
