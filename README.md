# Receiving and displaying ambient data;
# on a Raspberry Pi 4B-4GB

by Paulus Schulinck (Github handle: @PaulskPt)

This is a port from the [repo](https://github.com/PaulskPt/Presto_MQTT_multi_topic_subscriber/tree/main) for use with a Raspberry Pi 4B.

## What is it?
- Receiving, interpreting and displaying ambient data as temperature, pressure and humidity from a remote ambient sensor,
- Receiving $SYS topic MQTT messages,
- by means of MQTT messages.
- Using ambient data: temperatrue, pressure and humidity from a sensor on a Raspberry Sense Hat V2 board.

## MQTT messages come by "topics".
### This repo works with four different topics for the Publisher device and six topics for the Subscriber device:
- "sensor/Feath/ambient". Containing ambient data from a remote sensor
- "lights/Feath/toggle". Containing a lights toggle command from a remote controller
- "ligths/Feath/color_inc". Containing a lights color increase command from a remote controller
- "lights/Feath/color_dec". Containing a lights color decrease command from a remote controller
- "$SYS/broker/clients/disconnected". Subscriber device only. 
- "$SYS/broker/clients/connected". Subscriber device only.

If you do not know what is the MQTT communication protocol see: [MQTT](https://en.wikipedia.org/wiki/MQTT).

For a successful MQTT communication you need: 
- a MQTT Publisher device. In my case: an Adafruit Feather ESP32-S3 TFT board;
- a MQTT Broker device. This can be an online broker or a Broker device in your Local Area Network (LAN). I prefered the latter. In my case: a Raspberry Pi Compute Module 5.
- one or more MQTT Subscriber device(s). This repo is intended to use a Pimoroni Presto as MQTT Subscriber device.

## How to install?

For info on howto install software on the Publisher device and more info about the used Broker device see [repo](https://github.com/PaulskPt/Presto_MQTT_multi_topic_subscriber/tree/main)

Instructions to install and setup the Raspberry Sense Hat V2 see [here](https://www.raspberrypi.com/documentation/accessories/sense-hat.html).

### for the Subscriber device

You need a Raspberry Pi 4 or 5 with a Raspberry Pi Sense Hat V2.

You need to install a venv in folder ```/home/<user>/env```.


Next step, for this subscriber device, copy the files of this repo from this subfolder [here](https://github.com/PaulskPt/RPi4B_MQTT_multi_topic_subscriber/tree/main/src/subscriber) to the following  directory: 
```
/home/<User>/env/mqtt
```

### requirements for the development platform
You need to have installed on your Raspberry Pi: 
- Thonny IDE, Geany or equivalent.
- Have /boot/firmware/config.txt prepared for use of the Raspberry Sense Hat V2 as instructed in the documentation [here](https://www.raspberrypi.com/documentation/accessories/sense-hat.html)

Before to start the Python script ```mqtt_rpi4b.py``` you need to start a terminal session. Then go to the home directory, activate the virtual environment venv, cd to the mqtt directory and run the Python script:
```
	cd ~/
	source env/bin/activate
	cd env/mqtt
	python3 mqtt_rpi4b.py
```

As soon as the Python script runs and after it has setup/checked network interface communication, connection with the MQTT broker, load settings from ```secrets.json```, the following texts will be printed to the terminal:
```

(env) <user>@RPi4B:~/env/mqtt $ python3 mqtt_rpi4b.py
file: "sys_broker.json" has been reset.
global(): we are using the Raspberry Pi sense Hat
global(): using average tph values
topic0 = sensors/Feath/ambient
topic1 = lights/Feath/toggle
topic2 = lights/Feath/color_inc
topic3 = lights/Feath/color_dec
topic4 = $SYS/broker/clients/connected
topic5 = $SYS/broker/clients/disconnected
Connected to network through 'eth0'. IP: 192.168._.___
setup(): Connecting to MQTT local broker on port 1883
setup(): Not deleting log files, flag: "delete_logs" = False
setup(): Successfully connected to MQTT broker.
setup(): Subscribed to topic: "sensors/Feath/ambient"
setup(): Subscribed to topic: "lights/Feath/toggle"
setup(): Subscribed to topic: "lights/Feath/color_inc"
setup(): Subscribed to topic: "lights/Feath/color_dec"
setup(): Subscribed to topic: "$SYS/broker/clients/connected"
setup(): Subscribed to topic: "$SYS/broker/clients/disconnected"
Network OK
MQTT OK
Waiting for Messages...
-----------------------------------------------------------------------------------------------------------
Connected to broker 192.168.1.114 with result code: 'Success'
Subscribed: 1 [ReasonCode(Suback, 'Granted QoS 0')]
Subscribed: 2 [ReasonCode(Suback, 'Granted QoS 0')]
Subscribed: 3 [ReasonCode(Suback, 'Granted QoS 0')]
Subscribed: 4 [ReasonCode(Suback, 'Granted QoS 0')]
Subscribed: 5 [ReasonCode(Suback, 'Granted QoS 0')]
Subscribed: 6 [ReasonCode(Suback, 'Granted QoS 0')]
Subscribed: 7 [ReasonCode(Suback, 'Granted QoS 0')]
mqtt_callback(): Received a mqtt message on topic: "sensors/Feath/ambient"
Network OK
MQTT OK
MQTT  21:52:16
Feather PC-Lab BME280
msgID: 1753739536
Temperature: 30.3 °C
Pressure: 1002.2 mB
Altitude:  92.2 m
Humidity:  37.9 %
ext mqtt tph sensor data..........................: temp:  30.30, pres: 1002.20, humi:  37.90, alti:  92.20
Sense HAT tph data................................: temp:  34.40, pres: 1006.96, humi:  38.61
Average of ext tph sensor and sense hat tph sensor: temp:  32.35, pres: 1004.58, humi:  38.25
-----------------------------------------------------------------------------------------------------------
mqtt_callback(): Received a mqtt message on topic: "sensors/Feath/ambient"
MQTT  21:53:16
Feather PC-Lab BME280
msgID: 1753739596
Temperature: 30.3 °C
Pressure: 1002.2 mB
Altitude:  92.5 m
Humidity:  38.0 %
ext mqtt tph sensor data..........................: temp:  30.30, pres: 1002.20, humi:  38.00, alti:  92.50
Sense HAT tph data................................: temp:  34.57, pres: 1006.92, humi:  38.63
Average of ext tph sensor and sense hat tph sensor: temp:  32.44, pres: 1004.56, humi:  38.31
-----------------------------------------------------------------------------------------------------------
[...]
rotate_log_if_needed(): size of "mqtt_log_2025-07-27T231001.txt" is: 29294 bytes. Max size is: 51200 bytes.
mqtt_callback(): Received a mqtt message on topic: "sensors/Feath/ambient"
MQTT  21:58:16
Feather PC-Lab BME280
msgID: 1753739896
Temperature: 30.2 °C
Pressure: 1002.2 mB
Altitude:  92.7 m
Humidity:  38.1 %
ext mqtt tph sensor data..........................: temp:  30.20, pres: 1002.20, humi:  38.10, alti:  92.70
Sense HAT tph data................................: temp:  34.45, pres: 1006.88, humi:  38.68
Average of ext tph sensor and sense hat tph sensor: temp:  32.33, pres: 1004.54, humi:  38.39
-----------------------------------------------------------------------------------------------------------
[...]
```

# MQTT message content
For more info about MQTT message content see my other [repo](https://github.com/PaulskPt/Presto_MQTT_multi_topic_subscriber/tree/main)


# MQTT Subscriber 
The RPi4B, in the role of MQTT Subscriber, runs on Python3. The script for this Subscriber device does not display sensor data on the 8x8 led matrix during night hours.

The choice to use a "local MQTT broker" or an "external MQTT broker" is defined in the file "secrets.json".
In the script these lines load the broker choice and print info about this choice as shown below:
```
250 # MQTT setup
251 use_local_broker = mqtt_config_dict['use_local_broker']
252 #print(f"type(use_local_broker) = {type(use_local_broker)}")
253 if my_debug:
254   if use_local_broker:
255      print("Using local Broker")
256   else:
257      print("Using external Broker")
258
259 if use_local_broker:
260    BROKER = mqtt_config_dict['broker_local'] # Use the mosquitto broker app on the RaspberryPi CM5
261 else:
262    BROKER = mqtt_config_dict['broker_external']

```
The "publisher_id" and "subscriber_id" are also defined in the file "secrets.json". They are read into the script as follows:
```
	279 CLIENT_ID = bytes(secrets['mqtt']['client_id'], 'utf-8')
	280 PUBLISHER_ID = secrets['mqtt']['publisher_id']

```
This Python script will start logging in the current working directory. Log filenames contain a date and time. When the logfile becomes of a certain file length, a new logfile will be created. Another file, name: "mqtt_latest_log_fn.txt" will contain the filename of the current logfile. At the moment you force the running script to stop, by issuing the key-combo "<Ctrl+C>", this will provoke a KeyboardInterrupt. In this case the contents of the current logfile will be printed to the Terminal window. In principle, the logfile(s) created will not be deleted by the Python script, leaving you the opportunity to copy them to another device or just read them once again. If you want old logfile(s) to be deleted automatically, set the following boolean flag to True: 
```
	97 delete_logs = False
```
Beside these type of logfiles there exists also an "err.log" file.

Example of the contents of the file: "mqtt_latest_log_fn.txt":
```
	mqtt_log_2025-07-20T172657.txt
```

Example of the contents of the current log showed after a KeyboardInterrupt:
```
	loop(): KeyboardInterrupt: exiting...
	
	Size of log file: 8313. Max log file size can be: 51200 bytes.
	Contents of log file: "/sd/mqtt_log_2025-07-20T172657.txt"
	pr_log():  01) ---Log created on: 2025-07-20T17:26:57---
	pr_log():  02) 
	pr_log():  03) 2025-07-20T17:31:25 WiFi connected to: _____________
	pr_log():  04) 2025-07-20T17:31:25 Connected to MQTT broker: 192.168._.___
	pr_log():  05) 2025-07-20T17:31:26 Subscribed to topic: sensors/Feath/ambient
	pr_log():  06) 2025-07-20T17:31:26 Subscribed to topic: lights/Feath/toggle
	pr_log():  07) 2025-07-20T17:31:26 Subscribed to topic: lights/Feath/color_inc
	pr_log():  08) 2025-07-20T17:31:26 Subscribed to topic: lights/Feath/color_dec
	pr_log():  09) 2025-07-20T18:05:37 Session interrupted by user — logging and exiting.
	[...]
```
- Debug output: If you want more output to the serial output (Thonny Shell window), set the following boolean variable to True:
```
	95 my_debug = False
```

## File secrets.json
```
{
  "mqtt": {
    "use_local_broker" : 1,
    "broker_local" : "192.168._.___",
    "broker_external": "5.196.78.28",
    "port": "1883",
    "topic0": "sensors/Feath/ambient",
    "topic1": "lights/Feath/toggle",
    "topic2": "lights/Feath/color_inc",
    "topic3": "lights/Feath/color_dec",
    "topic4": "$SYS/broker/clients/connected",
	"topic5": "$SYS/broker/clients/disconnected",
    "client_id":  "RPi4BMQTTClient",
    "publisher_id": "Feath"
  },
  "wifi" : {
      "ssid" : "<Your WiFi SSID here>",
      "pass" : "<Your WiFi Password here>"
  },
  "display" : {
    "gotosleep": 23,
    "wakeup": 7
  },
  "hardware": {
    "network_interface" : "eth0",
    "use_sense_hat": 1
  },
  "tph_values": {
	  "average" : 1
  }
}
```
Note: under the key "mqtt", subkey "broker_local" fill-in the IP-address of your local broker device. Under "hardware" subkey "network_interface" default is set for an ethernet (wired) connection, however you can chose for a WiFi connection. In case of a WiFi connection,
fill-in the WiFi SSID and the WiFi Password, then fill-in under key "hardware", subkey "network_interface" : "wlan0" instead of "eth0".

A word about the key "tph_values", subkey "average". This MQTT Subscriber receives ambient sensor data (temperature, pressure, humidity) from an remote sensor through MQTT messages. The Raspberry Sense Hat V2 has also an ambient sensor.
The Python script will print to the Terminal window the sensor values from both the remote sensor and the Sense Hat sensor. The "average" subkey has by default a value of 1 which means that the average of the tph values of both remote and Sense hat sensors will be displayed on the 8x8 led matrix of the sense hat. They will also be printed to the terminal window.

## File sys_broker.json

The file "/sys_broker.json" will be cleared at the start of the Subscriber script. As soon as arrive a $SYS topic message of one of the $SYS topics subscribed, the topic name and its value will be added to sys_broker.json. As soon as the running of the sketch is interrupted by a key-combo: <Ctrl+C>, the contents of the file sys_broker.json will be printed to terminal window.

```
sys_broker_dict written to file: "sys_broker.json"
Size of sys_broker json file: 40.
Contents of sys_broker json file: "/sys_broker.json"
pr_log():  01) {"sys_broker": {"clients/connected": 2}}
```

# MQTT Broker

For more info see the [repo](https://github.com/PaulskPt/Presto_MQTT_multi_topic_subscriber/tree/main)


- Broker reset: in the case you reset or reboot your local broker device: wait until the local broker is running. Then reset both the MQTT Publisher device and the MQTT Subscriber(s) device(s) so that they report themselves to the MQTT local broker device as Publisher and Subscriber(s).

# End of use
Stop the execution of the Python script with pressing the key-combo <Ctrl+C>.
You will see output like this:
```
^Cloop(): KeyboardInterrupt: exiting...

sys_broker_dict written to file: "sys_broker.json"
pr_log(): sys_broker json file not found or unable to open. Error: [Errno 2] No such file or directory: '/sys_broker.json'
Size of log file: 29368.
Contents of log file: "/home/<user>/env/mqtt/mqtt_log_2025-07-27T231001.txt"
pr_log():  01) ---Log created on: 2025-07-27T23:10:01---
pr_log():  02)
pr_log():  03) 2025-07-27T23:14:15 connected to network. ip = 192.168._.___
pr_log():  04) 2025-07-27T23:14:15 Connected to MQTT broker: 192.168._.___
pr_log():  05) 2025-07-27T23:14:15 Subscribed to topic: sensors/Feath/ambient
pr_log():  06) 2025-07-27T23:14:15 Subscribed to topic: lights/Feath/toggle
pr_log():  07) 2025-07-27T23:14:15 Subscribed to topic: lights/Feath/color_inc
pr_log():  08) 2025-07-27T23:14:15 Subscribed to topic: lights/Feath/color_dec
pr_log():  09) 2025-07-27T23:14:15 Subscribed to topic: $SYS/broker/clients/connected
pr_log():  10) 2025-07-27T23:14:15 Subscribed to topic: $SYS/broker/clients/disconnected
pr_log():  11) 2025-07-27T23:21:18 Session interrupted by user — logging and exiting.
--------------------------------------------------
Traceback (most recent call last):
  File "/home/<user>/env/mqtt/mqtt_rpi4b.py", line 1700, in <module>
    while True:
KeyboardInterrupt

(env) <user>@RPi4B:~/env/mqtt $ 

```
Then stop the virtual environment by: 
``` 
(env) <user>@RPi4B:~/env/mqtt $ deactivate

``` 
then you will see:
```
<user>@RPi4B:~/env/mqtt $

```

# Hardware used

- A Raspberry Pi 4B-4GB [info](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
- A Raspberry Pi Sense Hat V2 [info](https://www.raspberrypi.com/products/sense-hat/)
- For the other hardware: Publisher device, Broker device, RTC unit, Gamepad QT, multi-sensor-stick and 3-port Grove Hub, see [repo](https://github.com/PaulskPt/Presto_MQTT_multi_topic_subscriber/tree/main<)

# Known problems

For more info see [repo](https://github.com/PaulskPt/Presto_MQTT_multi_topic_subscriber/tree/main)
