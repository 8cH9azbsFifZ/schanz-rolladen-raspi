import time
import paho.mqtt.client as mqtt
import logging
import subprocess

logging.basicConfig(level=logging.DEBUG, format='Rollershutter(%(threadName)-10s) %(message)s')

class Rollershutter():
    frequency = "433.9500e6"
    data_path = "/home/pi/schanz-rolladen-raspi/data"

    def __init__(self, TimeUpwards = 10. , TimeDownwards = 10., MQTThostname = "t20", RollershutterName="Test1"):

        # Connect to MQTT broker
        port = 1883
        self._client = mqtt.Client()
        self._client.connect(MQTThostname, port, 60)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._samplingrate = 0.01 # delay for the core loop 

        # Current state
        self.Name = RollershutterName
        self._percentage = 0
        self._moving_upwards = False # Current movement upwards?
        self._moving_downwards = False 
        self._time_upwards = TimeUpwards
        self._velocity_upwards = 1./TimeUpwards
        self._time_downwards = TimeDownwards
        self._velocity_downwards = 1./TimeDownwards

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
        logging.debug("MQTT>: " + ttopic + " ###> " + mmessage)
        self._client.publish(ttopic, mmessage)

    def _on_message(self, client, userdata, msg):
        """
        Receive MQTT control messages.
        Start with debugging on commandline using:
        mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Down
        """
        logging.debug(">MQTT: " + msg.payload.decode())
        self._time_lastcommand = time.time()
        if msg.payload.decode() == "Stop":
            self.Stop()
        if msg.payload.decode() == "Up":
            self.Up()
        if msg.payload.decode() == "Down":
            self.Down()
        if msg.payload.decode() == "Percent": # FIXME
            self.Percent()

    def _calc_current_percentage (self):
        curtime = time.time()
        self._time_t0 = self._time_t1
        self._time_t1 = curtime
        dt = self._time_t1 - self._time_t0
        if self._moving_downwards:
            moved_percentage = dt * self._velocity_downwards
            self._percentage -= moved_percentage 
            if self._percentage < 0.0:
                self._percentage = 0.0
                self._moving_downwards = False
        if self._moving_upwards:
            moved_percentage = dt * self._velocity_upwards
            self._percentage += moved_percentage 
            if self._percentage > 1.0:
                self._percentage = 1.0
                self._moving_upwards = False
        
    def Down(self):
        logging.debug("Rollershutter: down")
        self._moving_downwards = True
        self._press_button_up()

    def Up(self):
        logging.debug("Rollershutter: up")
        self._moving_upwards = True
        self._press_button_up()

    def Stop(self):
        logging.debug("Rollershutter: stop")
        if self._moving_upwards:
            self._press_button_down()
            self._moving_upwards = False
        if self._moving_downwards:
            self._press_button_up()
            self._moving_downwards = False                

    def Percent(self, percentage):
        logging.debug("Rollershutter: percent")
        # TODO implement
        pass

    def _core_loop(self):
        logging.debug("Start core loop")
        while True:
            self._client.loop(self._samplingrate) #blocks for 100ms (or whatever variable given, default 1s)
            self._calc_current_percentage()
            self._sendmessage(topic="/percentage", message=str(self._percentage))

    def _press_button_up(self):
        logging.debug("Send button up signal")
        subprocess.run(['/usr/bin/sendiq', "-s", "250000" ,"-f", self.frequency, "-t", "u8", "-i", self.data_path+"/button1.iq"])
    
    def _press_button_down(self):
        logging.debug("Send button down signal")
        subprocess.run(['/usr/bin/sendiq', "-s", "250000" ,"-f", self.frequency, "-t", "u8", "-i", self.data_path+"/button2.iq"])


if __name__ == "__main__":
    print ("Run manual")
    r = Rollershutter()
    r._core_loop()