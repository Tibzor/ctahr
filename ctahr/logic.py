
import threading,time
import configuration

class CtahrLogic(threading.Thread):
    daemon = True
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.app = app
        self.temp_state = 'CHECK'
        self.hygro_state = 'CHECK'
        self.fan_vote = [False,False]
        self.fan = False
        self.heat = False
        self.dehum = False
        self.temp_targ_err = 0
        self.temp_ext_err = 0
        self.hygro_err = 0
        self.running = True
        self.block_dehum = False


    def update_temp(self):
        if self.temp_state == 'CHECK':
            self.fan_vote[0] = False
            self.heat = False
            self.block_dehum = False
            if self.temp_targ_err < -configuration.delta_targ_H:
                self.temp_state = 'CHILL'
            elif self.temp_targ_err > configuration.delta_targ_H:
                self.temp_state = 'WARM'

        elif self.temp_state == 'CHILL':
            if self.temp_ext_err < -configuration.delta_ext_H:
                self.temp_state = 'VENTILATE'
                self.block_dehum = True
            else:
                self.temp_state = 'CHECK'

        elif self.temp_state == 'WARM':
            if self.temp_targ_err > configuration.delta_freeze_H:
                self.temp_state = 'HEAT'
            elif self.temp_ext_err > configuration.delta_ext_H:
                self.temp_state = 'VENTILATE'
            else:
                self.temp_state = 'CHECK'

        elif self.temp_state == 'VENTILATE':
            if (abs(self.temp_targ_err) < configuration.delta_targ_L or
                abs(self.temp_ext_err) < configuration.delta_ext_L):
                self.temp_state = 'CHECK'
            else:
                self.fan_vote[0] = True

        elif self.temp_state == 'HEAT':
            if self.temp_targ_err < configuration.delta_freeze_L:
                self.temp_state = 'CHECK'
            else:
                self.heat = True


    def update_hygro(self):
        if self.hygro_state == 'CHECK':
            if (self.hygro_err < -configuration.delta_hygro and
                    not self.block.dehum):
                self.hygro_state = 'DEHUM'
            else:
                self.dehum = False

        elif self.hygro_state == 'DEHUM':
            if (self.hygro_err > 0 or self.block.dehum):
                self.hygro_state = 'CHECK'
            else:
                self.dehum = False


    def update_values(self):
        int_values = self.app.thermohygro_interior.get()
        ext_values = self.app.thermohygro_exterior.get()
        if int_values[3] != 0 and ext_values[3] != 0:
            with self.lock:
                self.int_hygro, self.int_temp = int_values[:2]
                self.ext_hygro, self.ext_temp = ext_values[:2]
            return True
        else:
            return False

    def do_math(self):
        self.temp_targ_err = configuration.temp_target - self.int_temp
        self.temp_ext_err = self.ext_temp - self.int_temp
        if self.temp_targ_err < -configuration.delta_targ_H:
            self.hygro_target = configuration.hygro_target_summer
        else:
            self.hygro_target = configuration.hygro_target_winter
        self.hygro_err = self.hygro_target - self.int_hygro


    def decide_ventilate(self):
        if self.fan_vote[0]:
            self.fan = True
        elif self.fan_vote[1] and not self.dehum:
            self.fan = True
        else:
            self.fan = False


    def stop(self):
        self.running = False
        self.fan = False
        self.heat = False
        self.dehum = False

    def run(self):
        while self.running:
            if self.update_values():
                self.do_math()
            self.update_temp()
            self.update_hygro()
            self.decide_ventilate()
            time.sleep(1)
        print "[-] Stopping logic module"
