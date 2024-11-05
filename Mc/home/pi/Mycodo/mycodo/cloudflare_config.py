import os 
import logging
import subprocess
import time
from config import BOOT_PATH
from config import INSTALL_DIRECTORY

class CloudFlareConfig:
    def __init__(self):
        self.logger = logging.getLogger('mycodo.daemon')
        self.logger.setLevel(logging.INFO)

        self.period_timer = time.time()
        self.ap_enabled = False
        self.config_file = os.path.join(BOOT_PATH, 'cloudflare.config')
        self.hostname_file = os.path.join(BOOT_PATH, 'hostname.config')
        
    def is_config_file(self):
        if os.path.isfile(self.config_file):
            return True
        else:
            return False
        
    def is_hostname_file(self):
        if os.path.isfile(self.hostname_file):
            return True
        else:
            return False
        
    def remove(self):
        try:
            result = subprocess.run(
                ['sudo', 'cloudflared', 'service', 'uninstall'],
                check=True,
                text=True,
                capture_output=True
            )
            print(f"{result.stdout}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")  
            return e.stderr
        
    def set_hostname(self):
        if self.is_hostname_file():
            try:
                result = subprocess.run(
                    ['sudo', 'cp',self.hostname_file,os.path.join(INSTALL_DIRECTORY, 'mycodo')],
                    check=True,
                    text=True,
                    capture_output=True
                )
                os.remove(self.hostname_file)
                print("File copied successfully.")
                return result.stdout
            
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")
                return e.stderr
        else:
            print(f"No HostName config File Found")

    def run_config(self):
        if self.is_config_file():
            self.remove()
            # Read the file content
            with open(self.config_file, 'r') as file:
                commands = file.read()
            # Execute the commands
            try:
                result = subprocess.run(commands, shell=True, check=True, text=True, capture_output=True)
                os.remove(self.config_file)
                print(f"{result.stdout} {result.stderr}")
                return result.stdout
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")  
                return e.stderr
        else:
            print(f"No Cloudflare config File Found")


