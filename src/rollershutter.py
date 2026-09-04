import time
import paho.mqtt.client as mqtt
import logging
import fhem
import os
import RPi.GPIO as GPIO # FIXME: only for raspi?

logging.basicConfig(level=logging.DEBUG, format='Rollershutter(%(threadName)-10s) %(message)s')

class Rollershutter():
    def __init__(self, TimeOpen = 53. , TimeClose = 53., MQTThostname = "t20", mqtt_port=1883, FHEMhostname = "minicul-raspi", fhem_port=8083, RollershutterName="Test1", Simulation = False, UseFhem = True, PIN_BCM_Up = 23, PIN_BCM_Down = 24, UseRelais = False):
        # Simulation mode for debugging
        self._simulation = Simulation
        if self._simulation:
            logging.debug("Simulation Mode: On")
        else:
            logging.debug("Simulation Mode: Off")

        # Connect to FHEM
        # FIXME: use fhem
        logging.debug("Starting FHEM connection to: " + FHEMhostname + " on port " + str(fhem_port))
        self._use_fhem = UseFhem
        logging.debug("Using FHEM? " + str(UseFhem))
        self._fhem = fhem.Fhem(FHEMhostname, protocol="http", port=fhem_port)
        self._setup_sigduino_fhem()

        # Connect to MQTT broker
        logging.debug("Starting MQTT connection to: " + MQTThostname + " on port " + str(mqtt_port))
        self._mqtt_hostname = MQTThostname
        self._mqtt_port = mqtt_port
        self._client = mqtt.Client()
        # Callbacks must be registered before connecting, otherwise the CONNACK
        # of a fast broker can be processed before on_connect is known.
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._connect_with_backoff(initial=True)
        self._samplingrate = 0.01 # delay for the core loop while the shutter is moving
        self._idle_samplingrate = 1.0 # while nothing moves there is no need to spin the CPU

        # Configure PINS (USB Interface)
        self._use_relais = UseRelais
        logging.debug("Using Relais? " + str(UseRelais))
        self._relais_sw_up_pin = PIN_BCM_Up 
        self._relais_sw_down_pin = PIN_BCM_Down 
        self._sw_press_duration = .5 # 1 second press the buttons before release
        if self._use_relais:
            GPIO.setmode(GPIO.BCM)
            time.sleep(1)
            GPIO.setup(self._relais_sw_up_pin, GPIO.OUT) 
            time.sleep(1)
            GPIO.setup(self._relais_sw_down_pin, GPIO.OUT) 
            time.sleep(1)
            self._relais_off(self._relais_sw_up_pin)
            self._relais_off(self._relais_sw_down_pin)

        # Current state
        logging.debug("Starting rollershutter logic for: " + RollershutterName + " with time open " + str(TimeOpen) + " and time close " + str(TimeClose))
        self.Name = RollershutterName
        self._target_percentage = 0
        self._moving_open = False
        self._moving_close = False 
        self._time_open = TimeOpen
        self._velocity_open = 1./TimeOpen
        self._time_close = TimeClose
        self._velocity_close = 1./TimeClose
        self._state = None
        self._last_published_percentage = None
        self._time_lastpublish = time.time()
        self._republish_interval = 30. # keep subscribers in sync without flooding
        self._update_state("stopped")
        self._update_percentage(0, initial_state = True)

        # Timers
        self._time_lastcommand = time.time()
        self._time_t0 = time.time()
        self._time_t1 = time.time()

    def _setup_sigduino_fhem(self):
        if not self._simulation: # FIXME use fhem variable
            self._fhem.send_cmd("define sigduino SIGNALduino /dev/ttyUSB0@57600") # FIXME: make configurable
            self._fhem.send_cmd("attr sigduino hardware miniculCC1101") # FIXME: make configurable
            self._fhem.send_cmd("attr sigduino verbose 4") # only needed during reverse engineering

    def _check_connection_sigduino_fhem(self):
        state = self._fhem.get_device_reading("sigduino")
        return_code = len(state)  # 0 if Query had no result
        if return_code == 0:
            return False
        else:
            return True

    def _update_state(self, state):
        changed = self._state != state
        self._state = state
        # Only announce real changes - see the flood note in _update_percentage.
        if changed:
            self._sendmessage(topic="/state", message=str(self._state))

    def _update_percentage(self, percentage, initial_state = False):
        if initial_state:
            self._percentage = 0
            self._percentage_t1 = 0

        self._percentage_t1 = self._percentage
        self._percentage = percentage
        percentage_0_100 = int(self._percentage*100.)
        # Publish only significant updates. Sending on every iteration flooded
        # the broker with tens of thousands of messages per second and kept a
        # CPU core busy: a pending write makes loop() return immediately, so the
        # sampling timeout never takes effect.
        if initial_state or percentage_0_100 != self._last_published_percentage:
            self._last_published_percentage = percentage_0_100
            self._sendmessage(topic="/percentage", message=str(percentage_0_100))

    def _republish(self):
        """ Repeat the current values, so a restarted subscriber is not left guessing """
        self._sendmessage(topic="/state", message=str(self._state))
        self._sendmessage(topic="/percentage", message=str(int(self._percentage*100.)))

    def _on_connect(self, client, userdata, flags, rc):
        """ Connect to MQTT broker and subscribe to control messages """
        logging.debug("Connected with result code " + str(rc))
        self._client.subscribe("rollershutter/control/" + self.Name)
        self._client.subscribe("rollershutter/control_position/" + self.Name)

    def _on_disconnect(self, client, userdata, rc):
        """ Log unexpected disconnects - the core loop takes care of reconnecting """
        if rc != mqtt.MQTT_ERR_SUCCESS:
            logging.warning("Unexpected MQTT disconnect (rc " + str(rc) + ")")

    def _connect_with_backoff(self, initial=False):
        """
        (Re)establish the MQTT connection, retrying with exponential backoff.

        This is what keeps the daemon usable after a broker outage. Without it a
        single dropped connection silences the rollershutter permanently: the
        process keeps running and Home Assistant still reports success, but no
        command ever reaches the motor again.
        """
        delay = 1.
        while True:
            try:
                if initial:
                    self._client.connect(self._mqtt_hostname, self._mqtt_port, 60)
                else:
                    self._client.reconnect()
                logging.info("MQTT connected to " + self._mqtt_hostname + ":" + str(self._mqtt_port))
                return
            except (OSError, mqtt.WebsocketConnectionError) as e:
                logging.warning("MQTT connect failed (" + str(e) + ") - retrying in " + str(delay) + "s")
                time.sleep(delay)
                delay = min(delay * 2., 60.)
                # A failed initial connect still leaves the broker address on the
                # client, so from here on plain reconnects are enough.
                initial = False

    def _sendmessage(self, topic="/none", message="None"):
        """ Send a message using MQTT """
        ttopic = "rollershutter/" + self.Name + topic
        mmessage = str(message)
        self._time_lastpublish = time.time()
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
        elif msg.payload.decode() == "": # no parameter given
            logging.debug("  no parameter given - skipped: " + msg.payload.decode())
        else:
            logging.debug("  parameter not valid: " + msg.payload.decode())

    def _calc_current_percentage (self):
        curtime = time.time()
        self._time_t0 = self._time_t1
        self._time_t1 = curtime
        dt = self._time_t1 - self._time_t0

        # Update estimated positions - moving to closed state
        if self._moving_close:
            moved_percentage = dt * self._velocity_close
            self._percentage += moved_percentage 
            if self._percentage > self._target_percentage: 
                self._percentage = self._target_percentage
                if self._moving_close and self._target_percentage < 1.0: 
                    logging.debug("Rollershutter: stopping moving close, as target percentage reached")
                    self.Stop()
                else: 
                    self._moving_close = False
                self._update_percentage (self._percentage)

        # Update estimated positions - moving to open state
        if self._moving_open:
            moved_percentage = dt * self._velocity_open
            self._percentage -= moved_percentage 
            if self._percentage < self._target_percentage: 
                self._percentage = self._target_percentage
                if self._moving_open and self._target_percentage > 0.0:
                    logging.debug("Rollershutter: stopping moving open, as target percentage reached")
                    self.Stop()
                else:
                    self._moving_open = False
                self._update_percentage (self._percentage)

        
    def Close(self, target_percent = 1.0):
        logging.debug("Rollershutter: close")
        # Reset the time base, so the idle gap is not counted as travel time.
        self._time_t1 = time.time()
        self._moving_close = True
        self._update_state("closing")
        self._target_percentage = target_percent
        self._press_button_close()

    def Open(self, target_percent = 0.0):
        logging.debug("Rollershutter: open")
        # Reset the time base, so the idle gap is not counted as travel time.
        self._time_t1 = time.time()
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
            # Poll frequently while moving to keep the position estimate sharp,
            # but stay idle otherwise instead of burning a full CPU core.
            moving = self._moving_close or self._moving_open
            rc = self._client.loop(self._samplingrate if moving else self._idle_samplingrate)
            if rc != mqtt.MQTT_ERR_SUCCESS:
                # Never keep looping on a dead connection: once the socket is
                # gone, loop() would return the same error forever and the
                # daemon would silently stop reacting to any command.
                logging.warning("MQTT loop returned rc " + str(rc) + " - reconnecting")
                self._connect_with_backoff()
                continue

            self._calc_current_percentage()
            if self._moving_close or self._moving_open:
                self._update_percentage (self._percentage)

            # Set status of final positions
            if self._percentage == 0.0:
                self._update_state("open")
            if self._percentage == 1.0:
                self._update_state("closed")

            # Refresh subscribers now and then, so a restarted Home Assistant
            # learns the position without waiting for the next movement.
            if time.time() - self._time_lastpublish >= self._republish_interval:
                self._republish()

    def _press_button_open(self):
        open_command = "set sigduino sendMsg P46#111010101110001010#R10"
        if self._use_fhem: 
            self._fhem.send_cmd(open_command) 
        if self._use_relais:
            self._press_button_open_relais()
        
    def _press_button_close(self):
        # FIXME: sometimes this command stops working, until we press buttons on the original remote?
        close_command = "set sigduino sendMsg P46#111010101110001000#R10"
        if self._use_fhem: 
            self._fhem.send_cmd(close_command) 
        if self._use_relais:
            self._press_button_close_relais()

    def _relais_on(self, pin):
        GPIO.output(pin, GPIO.LOW)    
        
    def _relais_off(self, pin):
        GPIO.output(pin, GPIO.HIGH)

    def _press_button_close_relais(self):
        logging.debug("Send button close signal using relais")
        self._relais_on(self._relais_sw_down_pin)
        time.sleep(self._sw_press_duration)
        self._relais_off(self._relais_sw_down_pin)

    def _press_button_open_relais(self):
        logging.debug("Send button open signal using relais")
        self._relais_on(self._relais_sw_up_pin)
        time.sleep(self._sw_press_duration)
        self._relais_off(self._relais_sw_up_pin)


if __name__ == "__main__":
    vMQTT_HOST = os.getenv("MQTT_HOST", "t20")
    vMQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    vUSEFHEM = True # FIXME #os.getenv("USEFHEM") # FIXME: default
    vFHEM_HOST = os.getenv("FHEM_HOST", "minicul-raspi")
    vFHEM_PORT = int(os.getenv("FHEM_PORT", 8083))
    vTIME_OPEN = int(os.getenv("TIME_OPEN", 53))
    vTIME_CLOSE = int(os.getenv("TIME_CLOSE", 53))
    vROLLERSHUTTER_NAME = os.getenv("ROLLERSHUTTER_NAME", "Test1")
    vSIMULATION = os.getenv("SIMULATION")# FIXME: default
    vUSERELAIS = os.getenv("USERELAIS")# FIXME: default
    vPIN_BCM_Up = int(os.getenv("PIN_BCM_UP", 23))
    vPIN_BCM_Down = int(os.getenv("PIN_BCM_DOWN", 24))


    r = Rollershutter(TimeOpen=vTIME_OPEN, TimeClose=vTIME_CLOSE, RollershutterName=vROLLERSHUTTER_NAME, \
                      MQTThostname=vMQTT_HOST, mqtt_port=vMQTT_PORT, FHEMhostname=vFHEM_HOST, fhem_port=vFHEM_PORT, \
                        Simulation=vSIMULATION, UseFhem=True, UseRelais=False, PIN_BCM_Up=vPIN_BCM_Up, PIN_BCM_Down=vPIN_BCM_Down)

    r._core_loop()