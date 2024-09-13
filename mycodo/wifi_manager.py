import os 
import logging
import subprocess
import time
from config import INSTALL_DIRECTORY
from cloudflare_config import CloudFlareConfig

class wifiMonitor:
    def __init__(self):
        self.logger = logging.getLogger('mycodo.daemon')
        self.logger.setLevel(logging.INFO)

        self.period_timer = time.time()
        self.ap_enabled = False
        self.ap_directory = os.path.join(INSTALL_DIRECTORY, 'mycodo/scripts/ap')
        self.wifi_directory = os.path.join(INSTALL_DIRECTORY, 'mycodo/scripts/wifi')
        self.logger.info("WIFI Monitor Initialized")
        response = CloudFlareConfig().run_config()
        self.logger.info("CloudFlare Config : {}".format(response))

    def Wifi(self):
        while 1:
            time.sleep(2)
            _mode = self.wlan_mode()
            if(_mode == "ap" and self.eth_running()):
                self.logger.info("switching to wifi mode")
                time.sleep(60)
                self.Disable_ap()

            if(_mode == None and not self.eth_running()):
                if(time.time() - self.period_timer >= 60):
                    try:
                        self.Configure_ap()
                        self.period_timer = time.time()
                    except Exception as e:
                        self.logger.info("Wifi Error %s" %(e))

    def wlan_mode(self):
        mode = None
        try:
            cmd = "hostname -I"
            IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
            if("192.168.4.1" in IP):
                mode = "ap"
                self.ap_enabled = True
            else:
                IP_1 = subprocess.check_output("hostname -I | awk '{print $1}'", shell=True).decode("utf-8")
                IP_2 = subprocess.check_output("hostname -I | awk '{print $2}'", shell=True).decode("utf-8")

                if(IP_1.strip() and IP_2.strip()):
                    mode = "wifi"
                    self.ap_enabled = False
                else:
                    mode = None
                    self.ap_enabled = False
            return mode
        except:
            return None

    def eth_running(self):
        try:
            cmd = 'ifconfig eth0 | grep BROADCAST'
            resp = subprocess.check_output(cmd, shell=True, text=True)
            if("RUNNING" in str(resp)):
                return True
            else:
                return False
        except Exception as e:
            return False

    def Configure_ap(self):
        ##Stop dnsmasq and hostapd
        cmd = "sudo systemctl stop dnsmasq"
        resp = subprocess.check_output(cmd, shell=True, text=True)
        cmd = "sudo systemctl stop hostapd"
        resp = subprocess.check_output(cmd, shell=True, text=True)

        #move dhcp file
        cmd = "cp "+ self.ap_directory +"/dhcpcd.conf /etc/dhcpcd.conf"
        resp = subprocess.check_output(cmd, shell=True, text=True)
        ##restart dhcp
        cmd = "sudo service dhcpcd restart"
        resp = subprocess.check_output(cmd, shell=True, text=True)

        ##configure dns
        cmd = "cp "+ self.ap_directory +"/dnsmasq.conf /etc/dnsmasq.conf"
        resp = subprocess.check_output(cmd, shell=True, text=True)
        ##restart dns
        cmd = "sudo systemctl start dnsmasq"
        resp = subprocess.check_output(cmd, shell=True, text=True)
        ##configure ap
        cmd = "cp "+ self.ap_directory +"/hostapd.conf /etc/hostapd/hostapd.conf"
        resp = subprocess.check_output(cmd, shell=True, text=True)
        ##default hostapd
        cmd = "cp "+ self.ap_directory +"/hostapd /etc/default/hostapd"
        resp = subprocess.check_output(cmd, shell=True, text=True)

        ##start services
        cmd = "sudo systemctl unmask hostapd"
        resp = subprocess.check_output(cmd, shell=True, text=True)
        cmd = "sudo systemctl enable hostapd"
        resp = subprocess.check_output(cmd, shell=True, text=True)
        cmd = "sudo systemctl start hostapd"
        resp = subprocess.check_output(cmd, shell=True, text=True)

        self.logger.info("AP mode Configured")


    def Disable_ap(self):
        cmd = 'sudo systemctl stop hostapd'
        resp = subprocess.check_output(cmd, shell=True, text=True)
        cmd = 'sudo systemctl  disable hostapd'
        resp = subprocess.check_output(cmd, shell=True, text=True)

        ##move wifi dhcp file
        cmd = "cp "+ self.wifi_directory +"/dhcpcd.conf /etc/dhcpcd.conf"
        resp = subprocess.check_output(cmd, shell=True, text=True)

        cmd = 'sudo systemctl daemon-reload'
        resp = subprocess.check_output(cmd, shell=True, text=True)

        cmd = 'sudo systemctl restart dhcpcd'
        resp = subprocess.check_output(cmd, shell=True, text=True)

        self.logger.info("WiFi mode Configured")
        
if __name__ == "__main__":
    wifiMonitor().Wifi()


