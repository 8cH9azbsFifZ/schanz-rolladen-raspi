import time
import paho.mqtt.client as mqtt
import logging
import fhem
import os

logging.basicConfig(level=logging.DEBUG, format='Rollershutter(%(threadName)-10s) %(message)s')

class Rollershutter():
    def __init__(self, TimeOpen = 53. , TimeClose = 53., MQTThostname = "t20", mqtt_port=1883, FHEMhostname = "minicul-raspi", fhem_port=8083, RollershutterName="Test1", Simulation = False):
        self._simulation = Simulation
        if self._simulation:
            logging.debug("Simulation Mode: On")
        else:
            logging.debug("Simulation Mode: Off")

        # Connect to FHEM
        logging.debug("Starting FHEM connection to: " + FHEMhostname + " on port " + str(fhem_port))
        self._fhem = fhem.Fhem(FHEMhostname, protocol="http", port=fhem_port)
        self._setup_signuino_fhem()

        # Connect to MQTT broker
        logging.debug("Starting MQTT connection to: " + MQTThostname + " on port " + str(mqtt_port))
        self._client = mqtt.Client()
        self._client.connect(MQTThostname, mqtt_port, 60)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._samplingrate = 0.01 # delay for the core loop 

        # Current state
        logging.debug("Starting rollershutter logic for: " + RollershutterName + " with time open " + str(TimeOpen) + " and time close " + str(TimeClose))
        self.Name = RollershutterName
        self._target_percentage = 0
        self._moving_open = False # Current movement upwards?
        self._moving_close = False 
        self._time_open = TimeOpen
        self._velocity_open = 1./TimeOpen
        self._time_close = TimeClose
        self._velocity_close = 1./TimeClose
        self._update_state("stopped")
        self._update_percentage(0, initial_state = True)

        # Timers
        self._time_lastcommand = time.time()
        self._time_t0 = time.time()
        self._time_t1 = time.time()

    def _setup_signuino_fhem(self):
        if not self._simulation:
            self._fhem.send_cmd("define sigduino SIGNALduino /dev/ttyUSB0@57600") # FIXME
            self._fhem.send_cmd("attr sigduino hardware miniculCC1101") 
            #"attr sigduino verbose 4"

    def _update_state(self, state):
        self._state = state
        self._sendmessage(topic="/state", message=str(self._state))

    def _update_percentage(self, percentage, initial_state = False):
        if initial_state:
            self._percentage = 0
            self._percentage_t1 = 0

        # TODO: display only significant state updates
            
        self._percentage_t1 = self._percentage
        self._percentage = percentage
        percentage_0_100 = int(self._percentage*100.)
        self._sendmessage(topic="/percentage", message=str(percentage_0_100))

    def _on_connect(self, client, userdata, flags, rc):
        """ Connect to MQTT broker and subscribe to control messages """
        logging.debug("Connected with result code " + str(rc))
        self._client.subscribe("rollershutter/control/" + self.Name)
        self._client.subscribe("rollershutter/control_position/" + self.Name)

    def _sendmessage(self, topic="/none", message="None"):
        """ Send a message using MQTT """
        ttopic = "rollershutter/" + self.Name + topic
        mmessage = str(message)
        self._client.publish(ttopic, mmessage)

    def _on_message(self, client, userdata, msg):
        """
        Receive MQTT control messages.
        """
        logging.debug(">MQTT: " + msg.payload.decode())
        self._time_lastcommand = time.time()
        if msg.payload.decode() == "Stop":
            self.Stop()
            return 
        elif msg.payload.decode() == "Open":
            self.Open()
            return
        elif msg.payload.decode() == "Close":
            self.Close()
            return
        elif msg.payload.decode().isdigit():
            percent = float(msg.payload.decode()) / 100. # internally we use range [0,1], but externally [0,100]
            if 0.0 <= percent <= 1.0:
                self.SetPercent(percent)# internally we use range [0,1], but externally [0,100]
            else:
                logging.debug("  parameter not in range: " + msg.payload.decode())
        elif msg.payload.decode() == "Close":
            logging.debug("  no parameter given - skipped: " + msg.payload.decode())
        else:
            logging.debug("  parameter not valid: " + msg.payload.decode())

    def _calc_current_percentage (self):
        curtime = time.time()
        self._time_t0 = self._time_t1
        self._time_t1 = curtime
        dt = self._time_t1 - self._time_t0
        if self._moving_close:
            moved_percentage = dt * self._velocity_close
            self._percentage += moved_percentage 
            if self._percentage > self._target_percentage: 
                self._percentage = self._target_percentage
                if self._moving_close and self._target_percentage < 100.0: 
                    self.Stop()
                else: 
                    self._moving_close = False
                self._update_percentage (self._percentage)
        if self._moving_open:
            moved_percentage = dt * self._velocity_open
            self._percentage -= moved_percentage 
            if self._percentage < self._target_percentage: 
                self._percentage = self._target_percentage
                if self._moving_open and not self._target_percentage == 0.0:
                    self.Stop()
                else:
                    self._moving_open = False
                self._update_percentage (self._percentage)

        
        if self._percentage == 0.0:
            self._update_state("open")
        if self._percentage == 100.0:
            self._update_state("closed")

        
    def Close(self, target_percent = 1.0):
        logging.debug("Rollershutter: close")
        self._moving_close = True
        self._update_state("closing")
        self._target_percentage = target_percent
        self._press_button_close()

    def Open(self, target_percent = 0.0):
        logging.debug("Rollershutter: open")
        self._moving_open = True
        self._update_state("opening")
        self._target_percentage = target_percent
        self._press_button_open()

    def Stop(self):
        logging.debug("Rollershutter: stop")
        self._update_state("stopped")
        if self._moving_open:
            logging.debug("Rollershutter: stop - by pressing close button")
            self._press_button_close()
            self._moving_open = False
        elif self._moving_close:
            logging.debug("Rollershutter: stop - by pressing open button")
            self._press_button_open()
            self._moving_close = False      
        else:
            logging.debug("Rollershutter: not moving")

    def SetPercent(self, percentage):# internally we use range [0,1], but externally [0,100]
        logging.debug("Rollershutter: set to percent " + str(percentage) + " internally [0,1]")
        diff_percent = self._percentage - percentage
        if diff_percent < 0:
            self.Close(target_percent=percentage)
        if diff_percent > 0:
            self.Open(target_percent=percentage)

    def _core_loop(self):
        logging.debug("Start core loop")
        while True:
            self._client.loop(self._samplingrate) #blocks for 100ms (or whatever variable given, default 1s)
            self._calc_current_percentage()
            if self._moving_close or self._moving_open:
                self._update_percentage (self._percentage)

    def _press_button_open(self):
        open_command = "set sigduino sendMsg P46#111010101110001010#R10"
        if not self._simulation:
            self._fhem.send_cmd(open_command) 
        
    def _press_button_close(self):
        close_command = "set sigduino sendMsg P46#111010101110001000#R10"
        if not self._simulation:
            self._fhem.send_cmd(close_command) 

if __name__ == "__main__":
    vMQTT_HOST = os.getenv("MQTT_HOST", "t20")
    vMQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    vFHEM_HOST = os.getenv("FHEM_HOST", "minicul-raspi")
    vFHEM_PORT = int(os.getenv("FHEM_PORT", 8083))
    vTIME_OPEN = int(os.getenv("TIME_OPEN", 53))
    vTIME_CLOSE = int(os.getenv("TIME_CLOSE", 53))
    vROLLERSHUTTER_NAME = os.getenv("ROLLERSHUTTER_NAME", "Test1")
    vSIMULATION = os.getenv("SIMULATION")

    r = Rollershutter(TimeOpen=vTIME_OPEN, TimeClose=vTIME_CLOSE, RollershutterName=vROLLERSHUTTER_NAME, MQTThostname=vMQTT_HOST, mqtt_port=vMQTT_PORT, FHEMhostname=vFHEM_HOST, fhem_port=vFHEM_PORT, Simulation=vSIMULATION)

    r._core_loop()