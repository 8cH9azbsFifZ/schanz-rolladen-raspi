import time
import paho.mqtt.client as mqtt
import logging

logging.basicConfig(level=logging.DEBUG, format='Rollershutter(%(threadName)-10s) %(message)s')

class Rollershutter():
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
        self._time_downwards = TimeDownwards

        # Timers
        self._time_lastcommand = time.time()

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
        dt = curtime - self._time_lastcommand
        if self._moving_downwards:
            self._percentage = min(dt / self._time_downwards, 1.0)
        if self._moving_upwards:
            self._percentage = min(dt / self._time_upwards, 1.0)  
        
    def Down(self):
        logging.debug("Rollershutter: down")
        self._moving_downwards = True


    def Up(self):
        logging.debug("Rollershutter: up")
        self._moving_upwards = True
      

    def Stop(self):
        logging.debug("Rollershutter: stop")
        self._moving_upwards = False
        self._moving_downwards = False
        # TODO implement
        pass

    def Percent(self, percentage):
        logging.debug("Rollershutter: percent")
        # TODO implement
        pass

    def _core_loop(self):
        while True:
            self._client.loop(self._samplingrate) #blocks for 100ms (or whatever variable given, default 1s)
            self._calc_current_percentage()
            self._sendmessage(topic="/percentage", message=str(self._percentage))


if __name__ == "__main__":
    print ("Run manual")
    r = Rollershutter()
    #r._relais_on(r._relais1_pin)
    #time.sleep(1)
    #r._relais_off(r._relais1_pin)
    #time.sleep(1)
    #r._relais_on(r._relais2_pin)
    #time.sleep(1)
    #r._relais_off(r._relais2_pin)
    r._core_loop()