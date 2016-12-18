
import os,sys,time
import signal
import threading
from utils import ctxt,GREEN
import configuration
import RPi.GPIO as GPIO
from display import CtahrDisplay
from th_sensor import CtahrThermoHygroSensor
from relay import CtahrRelay
from logic import CtahrLogic
from security import CtahrSecurity

class CtahrApplication:

    def __init__(self):
        self.not_running = threading.Event()

        print "[+] Starting Ctahr"

        # gracefull shutdown signal handler
        signal.signal(signal.SIGTERM, self.shutdown)

        # Starting display manager
        self.display = CtahrDisplay()
        self.display.start()

        # Starting exterior sensor daemon
        self.thermohygro_exterior = CtahrThermoHygroSensor(
            configuration.thermohygro_sensor_exterior_pin)
        self.thermohygro_exterior.start()

        # Starting interior sensor daemon
        self.thermohygro_interior = CtahrThermoHygroSensor(
            configuration.thermohygro_sensor_interior_pin)
        self.thermohygro_interior.start()

        # Creating controlled output objects
        self.heater = CtahrRelay(configuration.heater_relay_pin)
        self.dehum = CtahrRelay(configuration.dehum_relay_pin)
        self.led_run = CtahrRelay(configuration.led_run_pin)

        # Starting regulation daemon
        self.logic = CtahrLogic(self)
        self.logic.start()

        # Starting security daemon
        self.security = CtahrSecurity(self)
        self.security.start()

        self.led_run_status = False


    def shutdown(self, signum, frame):
        # perform a gracefull shutdown here ;)

        print "[+] SIGNAL",signum,"received, shutting down gracefully"
        #
        self.not_running.set()

    def run(self):
        while not self.not_running.is_set():

            self.not_running.wait(1)

            self.led_run.activate(self.led_run_status)
            self.led_run_status = not self.led_run_status

            hygrotemp_int = self.thermohygro_interior.get()
            hygrotemp_ext = self.thermohygro_exterior.get()

            if hygrotemp_int != None and hygrotemp_ext != None:
                self.display.update_values(hygrotemp_int,hygrotemp_ext)

        print "[+] Ctahr as stopped"
        self.led_run.activate(False)
