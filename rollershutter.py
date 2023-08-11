import time
import paho.mqtt.client as mqtt
import logging
import fhem

logging.basicConfig(level=logging.DEBUG, format='Rollershutter(%(threadName)-10s) %(message)s')

class Rollershutter():
    mqtt_port = 1883
    fhem_port = 8083

    def __init__(self, TimeOpen = 53. , TimeClose = 53., MQTThostname = "t20", FHEMhostname = "raspimatic-raspi-wlan", RollershutterName="Test1"):
        # Connect to FHEM
        self._fhem = fhem.Fhem(FHEMhostname, protocol="http", port=self.fhem_port)

        # Connect to MQTT broker
        self._client = mqtt.Client()
        self._client.connect(MQTThostname, self.mqtt_port, 60)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._samplingrate = 0.01 # delay for the core loop 

        # Current state
        self.Name = RollershutterName
        self._percentage = 0
        self._target_percentage = 0
        self._moving_open = False # Current movement upwards?
        self._moving_close = False 
        self._time_open = TimeOpen
        self._velocity_open = 1./TimeOpen
        self._time_close = TimeClose
        self._velocity_close = 1./TimeClose

        # Timers
        self._time_lastcommand = time.time()
        self._time_t0 = time.time()
        self._time_t1 = time.time()

    def _on_connect(self, client, userdata, flags, rc):
        """ Connect to MQTT broker and subscribe to control messages """
        logging.debug("Connected with result code " + str(rc))
        self._client.subscribe("rollershutter/control/" + self.Name)

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
            percent = float(msg.payload.decode()) / 100.
            if 0.0 <= percent <= 1.0:
                self.Percent(percent)
            else:
                logging.debug("  parameter not in range: " + msg.payload.decode())
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
                if self._moving_close and not self._target_percentage == 100.0: 
                    self.Stop()
                else: 
                    self._moving_close = False
                self._sendmessage(topic="/percentage", message=str(self._percentage))
        if self._moving_open:
            moved_percentage = dt * self._velocity_open
            self._percentage -= moved_percentage 
            if self._percentage < self._target_percentage: 
                self._percentage = self._target_percentage
                if self._moving_open and not self._target_percentage == 0.0:
                    self.Stop()
                else:
                    self._moving_open = False
                self._sendmessage(topic="/percentage", message=str(self._percentage))
        
    def Close(self, target_percent = 1.0):
        logging.debug("Rollershutter: close")
        self._moving_close = True
        self._target_percentage = target_percent
        self._press_button_close()

    def Open(self, target_percent = 0.0):
        logging.debug("Rollershutter: open")
        self._moving_open = True
        self._target_percentage = target_percent
        self._press_button_open()

    def Stop(self):
        logging.debug("Rollershutter: stop")
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

    def Percent(self, percentage):
        logging.debug("Rollershutter: set to percent " + str(percentage))
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
                self._sendmessage(topic="/percentage", message=str(self._percentage))

    def _press_button_open(self):
        open_command = "set sigduino sendMsg P46#111010101110001010#R10"
        self._fhem.send_cmd(open_command) 
        
    def _press_button_close(self):
        close_command = "set sigduino sendMsg P46#111010101110001000#R10"
        self._fhem.send_cmd(close_command) 

if __name__ == "__main__":
    print ("Run manual")
    simulation = False
    TimeOpen = 53
    TimeClose = 53

    r = Rollershutter(TimeOpen=TimeOpen, TimeClose=TimeClose)
    r._core_loop()