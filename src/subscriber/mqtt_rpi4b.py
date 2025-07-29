# 2025-06-17 Downloaded from: https://github.com/digitalurban/Presto_MQTT_Display/blob/main/mqtt_presto.py
# by Andy Hudson-Smith going by @digitalurban
# Changes by Paulus Schulinck going by @PaulskPt
# Version 3.0  created on 2025-07-19.
# Includes handling MQTT messages with topics:
#         sensors/Feath/ambient,
#         lights/Feath/toggle,
#         lights/Feath/color_inc and
#         lights/Feath/color_dec
# Added functions to control the 7 ambient backlight LEDs
# by means of MQTT messages sent by a remote MQTT Publisher device.
#
# Ported for use on a Raspberri Pi 4B-4GB. 
# In case of using a Raspberry Pi 4B, printing log logs goes
# the current working directory.
#
# See also: https://github.com/eclipse-paho/paho.mqtt.python
import json
import time
import getcontext  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt
import subprocess
import netifaces
import os
import sys # See: https://github.com/dhylands/upy-examples/blob/master/print_exc.py
import time
from random import randint
import datetime

ip = '0.0.0.0'
topic = None
paho_msg = None 
mqttc = None

# Example where to extract the IP-address:
# if_dict[2][1]
# {'addr': '192.168.1.140', 'netmask': '255.255.255.0', 'broadcast': '192.168.1.255'}
def have_ip(printIt:bool = False):
    global ip
    ret = False
    this_ip = '0.0.0.0'
    if if_dict:
        if isinstance(if_dict, dict):
            if my_debug:
                print(f"have_ip(): if_dict = {if_dict}, type(if_dict) = {type(if_dict)}")
            if 2 in if_dict:
                this_ip = if_dict[2][1]['addr']  # e.g. 192.168.1.140
                if this_ip != '0.0.0.0':
                    if this_ip != ip:
                        ip = this_ip # update global ip
                    if printIt:
                        print(f"Connected to network through \'{interface}\'. IP: {ip}")
                    ret = True
    return ret

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    TAG = "on_connect(): "
    print(TAG+f"Connected to MQTT broker {BROKER} with result code: \'{reason_code}\'")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC_LST[0]) # was: ("$SYS/#")  sensors/Feath/ambient

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global msg_rcvd, topic, paho_msg, payload
    msg_rcvd = True
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    paho_msg = msg
    if my_debug:
        print(f"on_message(): type(msg) = {type(paho_msg)}, type(paho_msg.topic) = {type(paho_msg.topic)}, msg.topic = {paho_msg.topic}, str(payload) = {str(payload)}")
    #mqtt_callback(topic, paho_msg)
        
def on_subscribe(mqttc, obj, mid, reason_code_list, properties):
    print("on_subscribe(): subscribed: " + str(mid) + " " + str(reason_code_list))

def on_log(mqttc, obj, level, string):
    print(string)

"""
   deliveryComplete(IMqttDeliveryToken token) is called when the broker successfully gets your message published,
   this isn't called when the client had received your message. 
"""
TAG = "global(): "

WIDTH = HEIGHT = 480 # fictive values

BLACK = (0, 0, 0)
NAVY = (0, 0, 128)
ORANGE = (255, 180, 0)
LIGHTGREY = (211, 211, 211)
DARKGREY = (128, 128, 128)
BACKGROUND = (255, 250, 240)

my_debug = False
lStart = True
msg_rcvd = False
mqtt_connected = False # Flag to indicate if the MQTT client is connected   

_M_ID = 0
_VAL = 1
_TM = 2

topic_rcvd = None
topic_idx = -1

payload = None
payloadLst = []
globT = None
globP = None
globA = None
globH = None

use_sense_hat_data = True
if use_sense_hat_data:
    senseHatT = None
    senseHatP = None
    senseHatH = None 

datetime_empty = "0000-00-00T00:00:00"
publisher_datetime = None
publisher_time = None
publisher_msgID = None

NUM_LEDS = 7  # bl ambient neopixel leds
lights_ON = False # light toggle flag
lights_ON_old = False # remember light toggle flag state
lightsColorIdx = -1
lightsColorMin = 0
lightsColorMax = 9

blColorsDict = {0: (20,0,255),       # BLUE
			1: (255, 255, 255),  # WHITE
			2: (255,0,0),       # RED
			3: (245, 165, 4),    # ORANGE
			4: (0,255,0),        # GREEN
			5: (250, 125, 180),  # PINK
			6: (0,255,255),      # CYAN
			7: (255,0,255),      # MAGENTA
			8: (255, 255, 0),    # YELLOW
			9: (75, 75, 75)}     # GREY

blColorNamesDict = { 0: "BLUE",
                    1: "WHITE",
                    2: "RED",
                    3: "ORANGE",
                    4: "GREEN",
                    5: "PINK",
                    6: "CYAN",
                    7: "MAGENTA",
                    8: "YELLOW",
                    9: "GREY"}



ESSID = None 

"""
def is_connected_to_wifi():
    try:
        # Run iwgetid to get the current Wi-Fi ESSID
        ESSID = subprocess.check_output(["iwgetid", "-r"]).decode().strip()
        if ESSID:
            print(f"Connected to Wi-Fi network: {ESSID}")
            return True
        else:
            print("Not connected to any Wi-Fi network.")
            return False
    except subprocess.CalledProcessError:
        print("Wi-Fi interface not found or not connected.")
        return False
"""

def get_sensehat_data():
    global senseHatT,senseHatP, senseHatH
    # Get environmental data
    senseHatT = sense.get_temperature()
    senseHatP = sense.get_pressure()
    senseHatH = sense.get_humidity()

    senseHatT = round(senseHatT,2)
    senseHatP = round(senseHatP,2)
    senseHatH = round(senseHatH,2)

def clear_broker_json():
    ret = -1
    fn = "sys_broker.json"
    if my_debug:
        print("clear_broker_json(): entering...")
    try:
        sBroker = {"sys_broker": {}}  # create a clean sBroker
        with open(fn, "w") as fp:
            fp.write(json.dumps(sBroker))
        ret = 1
        if not my_debug:
            print(f"file: \"{fn}\" has been reset.")
    except OSError as exc:
        print(f"Error: {exc}")
    
    return ret

# Get the external definitions
#with open('secrets.json') as fp: # method I used, manually reads file content first, then parses it
#    secrets = json.loads(fp.read())
clear_broker_json()
time.sleep(1)
with open('sys_broker.json') as f:  # method used by Copilot. This reads and parses in one step
    sBroker = json.load(f)

# "$SYS/broker/" keys in sys_broker.json are loaded
# however these keys lack the "$SYS/broker/" prefix
sysBrokerDictModified = False

sys_broker_dict = sBroker.get("sys_broker", {})

if len(sys_broker_dict) > 0:
    if not my_debug:
        print("sys_broker_dict: key, value list = ")
        for k,v in sys_broker_dict.items():
            print(f"/$SYS/broker/{k} : {v}")

with open('secrets.json') as f:  # method used by Copilot. This reads and parses in one step
    secrets = json.load(f)

interface = secrets['hardware']['network_interface']
if_dict = netifaces.ifaddresses(interface)

use_sense_hat = True if secrets['hardware']['use_sense_hat'] == 1 else False
if use_sense_hat: 
    print("global(): we are using the Raspberry Pi sense Hat")
    from sense_hat import SenseHat
    sense = SenseHat()
    angles = [0, 90, 180, 270, 0, 90, 180, 270]
    sense.set_rotation(angles[2])

# Display the average values on the 8x8 led display (see function draw())
use_average = True if secrets['tph_values']['average'] == 1 else False
avg_t = "average" if use_average == True else "MQTT"
print(TAG+f"using {avg_t} tph values")

delete_logs = True if secrets['logging']['delete_logs'] == 1 else False

if my_debug:
    print(f"global(): type(use_sense_hat) = {type(use_sense_hat)}, use_sense_hat = {use_sense_hat}")

def clr_sense_hat():
   sense.clear(0,0,0) 

mqtt_config_dict = secrets.get("mqtt", {})

# MQTT setup
use_local_broker = mqtt_config_dict['use_local_broker'] # secrets['mqtt']['use_local_broker']
#print(f"type(use_local_broker) = {type(use_local_broker)}")
if my_debug:
    if use_local_broker:
        print("Using local Broker")
    else:
        print("Using external Broker")

if use_local_broker:
    BROKER = mqtt_config_dict['broker_local'] # secrets['mqtt']['broker_local']  # Use the mosquitto broker app on the RaspberryPi CM5
else:
    BROKER = mqtt_config_dict['broker_external'] # secrets['mqtt']['broker_external']
PORT = int(mqtt_config_dict['port']) # int(secrets['mqtt']['port'])

TOPIC_LST = []
#for i in range(5):
#    topicStr = "topic" + str(i)
#    #TOPIC_LST.append(bytes(secrets['mqtt'][topicStr], 'utf-8')) 
#    TOPIC_LST.append(secrets['mqtt'][topicStr]) 

# Loop through keys and create globals for keys starting with "topic"
for key, value in mqtt_config_dict.items():
    if key.startswith("topic"):
        #globals()[key] = value  # Dynamically assign global variable
        TOPIC_LST.append(value) 
        if not my_debug:
            print(f"{key} = {value}")

CLIENT_ID = bytes(mqtt_config_dict['client_id'],'utf-8') # bytes(secrets['mqtt']['client_id'], 'utf-8')
PUBLISHER_ID = mqtt_config_dict['publisher_id'] # secrets['mqtt']['publisher_id']

display_hrs_config_dict = secrets.get("display", {})
# print(f"display_hrs_config_dict.items() = {display_hrs_config_dict.items()}")
DISPLAY_HOUR_GOTOSLEEP = display_hrs_config_dict['gotosleep']
DISPLAY_HOUR_WAKEUP = display_hrs_config_dict['wakeup']
del display_hrs_config_dict

if my_debug:
    print(f"BROKER = {BROKER}")
    print(f"PORT = {PORT}, type(PORT) = {type(PORT)}")
    for i in range(len(TOPIC_LST)):
      print(f"TOPIC_LST[{i}] = {TOPIC_LST[i]}")
    print(f"CLIENT_ID = {CLIENT_ID}")
    print(f"PUBLISHER_ID = {PUBLISHER_ID}")

# Test the existance of a logfile
log_fn = None # Note: log_fn is set in the function create_logfile()
log_path = None # "/" + log_fn
log_size_max = 50 * 1024  # 51200 bytes # 50 kB max log file size
log_obj = None
log_exist = False
new_log_fn = None
new_log_path = None
new_log_obj = None
new_log_exist = False

def get_cwd():
    return os.getcwd()

def get_prefix():
    return get_cwd() + '/'

# Note: err_log_fn is used in the function create_err_log_file()
err_log_fn = "err_log.txt"
err_log_path = get_prefix() + err_log_fn
err_log_obj = None
# Note: ref_fn is used in the function create_ref_file()
ref_fn = "mqtt_latest_log_fn.txt"
ref_path = get_prefix() + ref_fn
ref_obj = None

ref_file_checked = False
log_file_checked = False


def do_line(nr:int = 5):
    if nr <= 0:
        return
    if nr < 5 or nr > 5:
        ln = '-' * nr
    else:
        ln = "----------" * 5
    print(ln)

def create_err_log_file():
    global err_log_fn, err_log_path, err_log_obj
    TAG = "create_err_log_file(): "
    try:
        if not ck_log(err_log_fn):
            # If the error log file does not exist, create it
            # err_log_fn = "err_log.txt"
            if err_log_obj:
                err_log_obj.close()
            with open(err_log_path, 'w') as ref_obj:
                err_log_obj.write('--- Error log file created on: {} ---\n'.format(get_iso_timestamp()))
                print(TAG+f"Error log file: \"{err_log_fn}\" created")
            if err_log_obj:
                err_log_obj.close() 
    except OSError as e:
        print(TAG+f"OSError: {e}")

def create_ref_file():
    global ref_path, ref_obj, ref_fn
    TAG = "create_ref_file(): "
    try:
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'w') as ref_obj:
            ref_obj.write('--- Reference file created on: {} ---\n'.format(get_iso_timestamp()))
            print(TAG+f"reference file: \"{ref_fn}\" created")
    except OSError as e:
        print(TAG+f"OSError: {e}")
        
def ref_file_exists():
    global ref_path, ref_obj, ref_fn
    ret = False
    TAG = "ref_file_exists(): "
    try:
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'r') as ref_obj:
            ret = True
        if ref_obj:
            ref_obj.close()
    except OSError as e:
        print(TAG+f"Reference file not found or unable to open. Error: {e}")
    return ret

def clear_ref_file():
    global ref_path, ref_obj, ref_fn
    TAG = "clear_ref_file(): "
    txt1 = "reference file: "
    try:
        ref_exist = ref_file_exists() # Check if the reference file exists
        if ref_exist:
            if my_debug:
                print(TAG+txt1+f"\"{ref_fn}\" exists, making it empty")
            # If the reference file exists, make it empty
            # Note: This will overwrite the existing file, so be careful!
            if ref_obj:
                ref_obj.close()
            with open(ref_path, 'w') as ref_obj:
                pass  # Create an empty reference file
            ref_obj.close()
            ref_size = os.stat(ref_path)[6]  # File size in bytes
            if ref_size == 0:
                print(TAG+txt1+f"\"{ref_fn}\" is empty")
            else:
                print(TAG+txt1+f"\"{ref_fn}\" is not empty, size: {ref_size} bytes")
        else:
            if my_debug:
                print(TAG+txt1+f"\"{ref_fn}\" does not exist, creating it")
            create_ref_file()    
    except OSError as e:
        print(TAG+f"OSError: {e}")

def get_active_log_filename():
    global ref_path, ref_obj, ref_fn, ref_file_checked, log_fn, log_path, log_exist
    TAG = "get_active_log_filename(): "
    txt1 = "Active log "
    txt2 = "reference file"
    txt3 = "in the directory:"
    ret = None
    active_log_fn = None
    active_log_path = None
    active_log_exist = False
    active_log_size = 0
    try:
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'r') as ref_obj:
            active_log_fn = ref_obj.readline().strip()  # Read the first line and remove trailing newline
        if ref_obj:
            ref_obj.close()
        ref_file_checked = True
        
        if active_log_fn:
            if my_debug:
              print(TAG + txt1 + f"filename read from " + txt2 + f": \"{active_log_fn}\"")
            # Check if the log file exists in the specified directory
            if active_log_fn in os.listdir(get_prefix()):
                active_log_path = get_prefix() + active_log_fn
                if my_debug:
                  print(TAG + txt1 + f"file: \"{active_log_fn}\" exists in " + txt3 + f"\"{get_prefix()}\"")
                active_log_size = os.stat(active_log_path)[6]  # File size in bytes
                if my_debug:
                  print(TAG + txt1 + f"Active log file: \"{active_log_fn}\" exists in " + txt3 + f"\"{get_prefix()}\"")
                  print(TAG+f"Active log file size: {active_log_size} bytes")
                # Set the log path and log exist flag
                active_log_path = get_prefix() + active_log_fn
                active_log_exist = True
                #ret = active_log_fn  # Return the active log filename
            else:
                print(TAG + txt1 + f"file: \"{active_log_fn}\" does not exist " + txt3 + f"\"{get_prefix()}\"")
                # If the log file does not exist, we can create a new one
                active_log_exist = False
                active_log_path = None
                active_log_fn = None
                clear_ref_file()

            ret = active_log_fn
            log_fn = active_log_fn
            log_path = active_log_path 
            log_exist = active_log_exist
        else:
            print(TAG + txt1 + "filename not found in the " + txt2)
    except OSError as e:
        print(TAG+f"Error reading the " + txt2 + ": {e}")
    
    return ret

def pr_ref():
    global ref_path, ref_obj
    ret = 0
    TAG = "pr_ref(): "
    try:
        if ref_obj:
            ref_obj.close()
        
        if ref_path:
            if my_debug:
              print(TAG+f"Contents of ref file: \"{ref_path}\":")
            f_cnt = 0
            with open(ref_path, 'r') as ref_obj:
                for line in ref_obj:
                    f_cnt += 1
                    #f_cnt_str = "0" + str(f_cnt) if f_cnt < 10 else str(f_cnt)
                    #print(f"   {f_cnt_str}) {line.strip()}") 
                    if my_debug:
                      print("{:s} {:02d}) {:s}".format(TAG, f_cnt, line.strip())) # Remove trailing newline for cleaner output
                if my_debug:
                  do_line()
            ret = f_cnt  # Return the number of lines printed
    except OSError as e:
        print(TAG+f"Reference file not found or unable to open. Error: {e}")
    return ret

# Function to get current datetime as an ISO string
def get_iso_timestamp():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*t[:6])

def new_logname():
    fn = "mqtt_log_{}.txt".format(get_iso_timestamp())
    # Replace ":" with "" for compatibility with MS Windows file systems
    return fn.replace(":", "")

def ck_log(fn):
    if isinstance(fn, str) and len(fn) > 0:
        if fn in os.listdir(get_prefix()):
            return True
    return False

# Create a new log file and add its filename to the ref file
def create_logfile():
    global log_fn, log_path, log_obj, log_exist, ref_path, ref_obj, new_log_fn, new_log_path, new_log_obj
    TAG = "create_logfile(): "
    
    new_log_fn = new_logname()
    if not my_debug:
        print(f"new_logname() = {new_log_fn}")
    
    new_log_path = get_prefix() + new_log_fn
    try:
        if log_obj:
            log_obj.close()
        with open(new_log_path, 'w') as log_obj:
            log_obj.write('---Log created on: {}---\n'.format(get_iso_timestamp()))
        print(TAG+f"created new log file: \"{new_log_fn}\"")
        # Check existance of the new log file
        if ck_log(new_log_fn):
            print(TAG+f"check: new log file: \"{new_log_fn}\" exists")
        else:
            print(TAG+f"check: new log file: \"{new_log_fn}\" not found!")
        # Make empty the ref file
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'w') as ref_obj: # Make empty the ref file
            pass
        if ref_obj:
            ref_obj.close()
        # Add the filename of the new logfile to the ref file
        with open(ref_path, "w") as ref_obj:
            ref_obj.write(new_log_fn)
            print(TAG+f"added to ref file: \"{ref_fn}\" the new active log filename \"{new_log_fn}\"")
            pr_ref()  # Print the contents of the ref file
    except OSError as e:
        print(TAG+f"OSError: {e}")
    """
    if new_log_fn is not None:
        log_fn = new_log_fn # Update the global log_fn variable
    if new_log_path is not None:
        log_path = new_log_path # Update the global log_path variable
    """

# Function to close a log file that is too long
# Then create a new log file
# Add the new log filename in the ref file
def rotate_log_if_needed(show: bool = False):
    global log_path, log_fn, log_size_max, log_obj, log_exist, ref_path, ref_fn, ref_obj, new_log_fn, new_log_path, new_log_obj
    TAG = "rotate_log_if_needed(): "
    if new_log_fn is not None: # new_log_fn could have be created in the part MAIN
        if ck_log(new_log_fn):
            log_fn = new_log_fn # Update the global log_fn variable
            current_log = new_log_fn # copy the current log filename
            current_log_path = new_log_path # copy the current log path
            log_exist = True
    elif log_exist and log_fn is not None:
        current_log = log_fn # copy the current log filename
        current_log_path = get_prefix() + current_log # copy the current log path
    if current_log:
        if my_debug:
            print(TAG+f"current log filename = \"{current_log}\"")
        if ck_log(current_log):
            log_size = os.stat(current_log_path)[6]  # File size in bytes
            if my_debug or show:
                print(TAG+f"size of \"{current_log}\" is: {log_size} bytes. Max size is: {log_size_max} bytes.")
            if log_size > log_size_max:
                if my_debug:
                    print(TAG+f"Log file: \"{current_log}\" is too long, creating a new log file")
                create_logfile()
                if my_debug:
                    print(TAG+f"Current log file: \"{current_log}\" is closed")
                    print(TAG+f"Log rotated to new log file: \"{log_path}\"")  # log_fn, log_path changed in create_logfile()
            else:
                if my_debug:
                  print(TAG+"rotate log file not needed yet")
        else:
            print(TAG+f"log_file: \"{log_fn}\" not found in listdir(\"{get_prefix()}\")")
            print(TAG+"creating a new log file")
            create_logfile() # log_fn, log_path changed in create_logfile()
    else:
        # log_fn is None
        print(TAG+"creating a new log file")
        create_logfile() # log_fn, log_path changed in create_logfile()
   
    if log_fn is None:
        print(TAG+"Log rotation failed:")

#------------------ MAIN START HERE ------------------
# The main function is not used in this script
# but the code is structured to allow for easy integration into a larger system.
TAG = "main(): "
my_list = None 
try:
    # Check the existance of a reference file
    # in which we save the file name of the latest log file created
    if ref_file_exists():
        # Reference file exists;   
        # File exists; open for appending
        active_log_fn = None
        active_log_path = None
        active_log_exist = False
        ref_exist = True
        ref_size = os.stat(ref_path)[6]  # File size in bytes
        if my_debug:
            print(TAG+f"ref file: \"{ref_fn}\" exists. Size: {ref_size} bytes")
        if ref_size > 0:
            nr_log_files = pr_ref()
            if my_debug:
              print(TAG+f"Number of log files listed in reference file: {nr_log_files}")
            if nr_log_files > 0:
                # read the log filename from the reference file
                active_log_fn = get_active_log_filename()  # Get the active log filename from the reference file
                # print(TAG+f"Active log filename extracted from reference file: \"{log_fn}\"")
                if active_log_fn is None:
                    # No log filename found in the reference file
                    print(TAG+f"No active log filename found in the reference file: \"{ref_fn}\"")
                else:
                    # Check if the active log file exists
                    if ck_log(active_log_fn):
                        active_log_path = get_prefix() + log_fn
                        active_log_exist = True
               
                # If the active log file exists, we can use it
                # Otherwise, we create a new log file
                if active_log_exist:
                    if my_debug:
                      print(TAG+f"Active log file: \"{active_log_fn}\" does exist in the directory: \"{get_prefix()}\"")
                    active_log_path = get_prefix() + active_log_fn
                    active_log_size = os.stat(active_log_path)[6]  # File size in bytes 
                    log_fn = active_log_fn  # Update the global log_fn variable
                    log_path = active_log_path  # Update the global log_path variable
                else:
                    print(TAG+f"Active log file: \"{active_log_fn}\" does not exist in the directory: \"{get_prefix()}\"")
                    print(TAG+f"creating a new log file")
                
                    active_log_exist = False
                    active_log_path = None
                    create_logfile()
        else:
            # There is no last log filename in the ref file.
            # Create a new log file and add to the ref file
            if log_fn and ck_log(log_fn):
                pass  # The log file exists, so we do not need to create a new one
            else:
                log_fn = new_logname() # "mqtt_log_{}.txt".format(get_iso_timestamp())
                log_path = get_prefix() + log_fn
            try:
                if ref_obj:
                    ref_obj.close()
                with open(ref_path, 'w') as ref_obj:
                    ref_obj.write(log_fn) # Add the log filename to the ref file
            except OSError as e:
                print(TAG+f"OSError: {e}")
    else:
        # ref_fn does not exist; create and write header
        # First:  create a new log filename
        # Second: add the log filename to the ref file
        log_fn = new_logname() # "mqtt_log_{}.txt".format(get_iso_timestamp())
        log_path = get_prefix() + log_fn
        try:
            if ref_obj:
                ref_obj.close()
            with open(ref_path, 'w') as ref_obj:
                ref_obj.write('--- Reference file created on: {} ---\n'.format(get_iso_timestamp()))
                ref_obj.write(log_fn) # And add the log filename to the ref file
            ref_exist = True
            if not my_debug:
                print(TAG+f"reference file: \"{ref_path}\" created")
                print(TAG+f"current log filename: \"{log_fn}\" added to ref file")
        except OSError as e:
            print(TAG+f"OSError: {e}")
        # rotate_log_if_needed() # create a new log file and add it to th ref file
except OSError as e:
    print(TAG+f"OSError occurred: {e}")
    
def timestamp():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5])
    
# Add data to log file
def add_to_log(txt:str = ""):
    global log_exist, log_path, log_fn, log_obj, log_size_max
    TAG = "add_to_log(): "
    param_type = type(txt)
    if isinstance(txt, str):
        if len(txt) > 0:
            size = os.stat(log_path)[6]  # File size in bytes
            if size >= log_size_max:
                rotate_log_if_needed() # check if we need to create a new log file
            
            if log_obj:
                log_obj.close()
            if ck_log(log_fn):
                try:
                    ts = timestamp()
                    with open(log_path, 'a') as log_obj:  # 'a' for append mode
                        log_obj.write('\n '+ ts + " " + txt)  # Add received msg to file /mqtt_log.txt
                    if my_debug:
                        print(TAG+f"data: \"{txt}\" appended successfully to the log file.")
                except OSError as e:
                    print(TAG+f"add_to_log(): error while trying to open or write to the log file: {e}")
            else:
                print(TAG+f"log file: \"{log_path}\" does not exist. Unable to add: \"{txt}\"")
    else:
        print(TAG+f"parameter txt needs to be of type str, received a type: {param_type}")

if my_list:
    my_list = None # Clear memory

client = None
# Initialize the default message
payload_txt = "Waiting for Messages..."
last_update_time = abs(time.time())
MESSAGE_DISPLAY_DURATION = 20  # Duration to display each message in seconds

# WiFi setup

# Eventually (if needed)
if interface == 'wlan0':
    ssid = secrets['wifi']['ssid']
    password = secrets['wifi']['pass']
    print(TAG+"Connecting to WiFi...")
elif interface == 'eth0':
    ssid = ""
    password = ""
    #if not is_connected_to_wifi():
    #    interface = 'wlan0'
    #    os.system('iwconfig ' + interface + ' essid ' + ssid + ' key ' + password)
    if have_ip(True):
        t = "connected to network. ip = {}".format(ip)
        add_to_log(t)
else:
    print("no network interface available!")
    raise RuntimeError

msg_drawn = False

# List log files starting with "mqtt_log"
def list_logfiles():
    TAG = "list_logfiles(): "
    err_log_present = False
    if err_log_fn:
        err_log_present = ck_log(err_log_fn)
    list_log_prefix = 'mqtt_log'
    list_log_path = ""

    try:
        files = os.listdir(get_prefix())
        log_files = [f for f in files if f.startswith(list_log_prefix) and f.endswith('.txt')]
        files = None  # Clear memory
        # do_line()
        cnt = 0
        if my_debug:
          print(TAG+"MQTT log files:")
        if err_log_present:
            cnt +=1
            log_size = os.stat(err_log_path)[6]
            if my_debug:
              print("{:2d}) {}, size {} bytes".format(cnt, err_log_fn, log_size), end='\n')
        for fname in log_files:
            #if fname.beginswith(list_log_prefix) and fname.endswith('.txt'):
            cnt += 1
            #print(TAG+f"fname = \"{fname}\"")
            #if ck_log(fname):
            list_log_path = get_prefix() + fname
            log_size = os.stat(list_log_path)[6]
            if my_debug:
              print("{:2d}) {}, size {} bytes".format(cnt, fname, log_size), end='\n')
        if my_debug:
          do_line(51)
          if cnt == 0:
              print(TAG+"No log files found starting with \"{}\"".format(list_log_prefix))
          else:
              print(TAG+"Total number of log files found: {}".format(cnt))
          do_line(51)
    except OSError as e:
        print(TAG+"Error accessing directory:", e)

def del_logfiles():
    global ref_fn, ref_path, ref_obj, log_fn
    TAG = "del_logfiles(): "
    
    log_dir = get_prefix()
    t = time.localtime()
    # year, month, day = t[0], t[1], t[2]
    # Or even more compactly:
    yy, mo, dd, *_ = time.localtime()

    print(TAG+f"log_dir = {log_dir}")
    log_pfx = "mqtt_log_" + str(yy) + "-" + "0" + str(mo) if mo < 10 else str(mo)  # + "-" + "0" + str(dd) if dd < 10 else str(dd)  # Change to desired year-month-day
    print(TAG+f"log_pfx = {log_pfx}")
    deleted_files = []

    try:
        files = os.listdir(log_dir)
        for fname in files:
            if fname.startswith(log_pfx) and fname.endswith('.txt'):
                if my_debug:
                    print(TAG+f"fname = \"{fname}\", log_fn = \"{log_fn}\"")
                if fname in log_fn:
                    print(TAG+f"We\'re not deleting the current logfile: \"{log_fn}\"")
                    continue
                full_path = '{}/{}'.format(log_dir, fname)
                try:
                    os.remove(full_path)
                    deleted_files.append(fname)
                except OSError as e:
                    print(TAG+f"Failed to delete: {fname}, error: {e}")

        if len(deleted_files) > 0:
            print(TAG+"Deleted files:")
            for f in deleted_files:
                print("  ✔", f)
            
            if ref_obj:
                ref_obj.close()
            with open(ref_path, 'w') as ref_obj:  # Make empty the ref file
                pass
            ref_size = os.stat(ref_path)[6]  # File size in bytes
            if my_debug:
                print(TAG+f"check ref file: \"{ref_fn}\" after making empty. Size: {ref_size} bytes")
        else:
            print(TAG+f"no logfile(s) found starting with \"{log_pfx}\" and ending with \".txt\"")
    
    except OSError as e:
        print(TAG+f"Could not list directory: {log_dir} for deletion. Error: {e}")
        
def save_broker_dict():
    global sBroker, sysBrokerDictModified
    ret = -1
    fn = "sys_broker.json"
    if not sysBrokerDictModified:
        return 1
    try:
        sBroker["sys_broker"] = sys_broker_dict  # Update the wrapper dict
        with open(fn, "w") as fp:
            fp.write(json.dumps(sBroker))
        ret = 1
    except OSError as exc:
        print(f"Error: {exc}")
        
    if ret == 1:
        if not my_debug:
            print(f"sys_broker_dict written to file: \"{fn}\"")
        sysBrokerDictModified = False # reset flag
    return ret

def broker_topic_in_db():
    global sBroker, sys_broker_dict, topic_rcvd, payload, sysBrokerDictModified
    TAG = "broker_topic_in_db(): "
    ret = -1
    if topic_rcvd.startswith("$SYS"):
        if payload:
            # "$SYS/broker/"
            short_key = topic_rcvd[len("$SYS/broker/"):]
            if "retained messages/count" == short_key: # correct this faulty topic (containing a space)
                faulty_key = short_key
                short_key = "messages/retained/count"
                if not my_debug:
                    print(TAG+f"changing faulty key: {faulty_key} into: {short_key}")
            if short_key in sys_broker_dict.keys():
                ret = 1
                sysBrokerDictModified = True
                old_value = sys_broker_dict[short_key]
                if my_debug:
                    print(TAG+f"topic_rcvd = \"{topic_rcvd}\", key = \"{short_key}\", old value = {old_value}")
                sys_broker_dict[short_key] = payload
                new_value = sys_broker_dict[short_key]
                if my_debug:
                    print(TAG+f"topic_rcvd = \"{topic_rcvd}\", key = \"{short_key}\", value updated to: {new_value}")
            else:
                sys_broker_dict[short_key] = payload
                sysBrokerDictModified = True
                ret = 1
        else:
            print(TAG+f"msg topic: \"{topic_rcvd}\", payload empty? : {payload}")
            
        if sysBrokerDictModified:
            if my_debug:
                print(TAG+f"topic_rcvd = \"{topic_rcvd}\", short_key \"{short_key}\", added to: sys_broker_dict")
    return ret 

def topic_in_lst():
    if topic_rcvd.startswith("$SYS"):
        return 1  # Accept all topic_rcvd starting with '$SYS'
    TAG = "topic_in_lst(): "
    ret = -1
    topic_idx = 0
    le = len (TOPIC_LST)
    if le > 0:
        for i in range(le):
            if TOPIC_LST[i] == topic_rcvd:
                ret = i
                break
    if my_debug:
        print(TAG+f"topic received: \"{topic_rcvd}\" ", end='')
    if ret < 0:
        if my_debug:
            print(" not ", end='')
    if my_debug:
        print("found in TOPIC_LST")
    return ret

# MQTT callback function
def mqtt_callback(topic, msg):
    global topic_rcvd, msg_rcvd, payload, last_update_time, topic_idx
    TAG = "mqtt_callback(): "
    payloadStr = ""
    last_time = ""
    last_update_time = 0
    
    try:
        if my_debug:
            print(TAG+f"type(topic) = {type(topic)}")
        if isinstance(topic, bytes):
            topic_rcvd = topic.decode("utf-8")
        elif isinstance(topic, str):
            topic_rcvd = topic # same
        n =  topic_in_lst()
        if n < 0:
            if my_debug:
                print(TAG+f"topic received {topic_rcvd} not subscribed to. Skipping...")
            return
        else:
            topic_idx = n
        
        #topic_rcvd = msg.topic
        #payload = msg.payload
        isInt = False
        isDict = False
        payload = json.loads(msg.payload)
        if my_debug:
            print(TAG+f"payload after json.load(msg.payload) = {payload}, type(payload) = {type(payload)}")
        if isinstance(payload, bytes):
            payloadStr = payload.decode['utf-8']
        elif isinstance(payload, int):
            isInt = True
            payloadStr = str(payload)
        elif isinstance(payload, dict):
            isDict = True
            payloadStr = str(list(payload.keys()))
        if payload is not None:
            last_update_time = int(time.time())  # Update the last update time
            #iso_time = datetime.datetime.fromtimestamp(last_update_time).isoformat()
            last_time = datetime.datetime.fromtimestamp(last_update_time).replace(microsecond=0)
            if my_debug:
                print(TAG+f"last_update_time = {last_update_time} = {last_time}")
            if my_debug:
                print(TAG+f"type(payload) = {type(payload)}")
            if broker_topic_in_db():
                if my_debug:
                    #t = "payload keys:" if isDict == True else "payloadStr:"
                    #print(TAG+f"topic_rcvd: \"{topic_rcvd}\", {t} \"{payloadStr}\"")
                    if isInt:
                        print(TAG+f"topic_rcvd: \"{topic_rcvd}\", payload: {payloadStr}")
                    else:
                        print(TAG+f"topic_rcvd: \"{topic_rcvd}\"")
        else:
            print(TAG+f"Incomplete message \"{msg}\" received, skipping.")
            return

        if topic.startswith("$SYS"):
            if isinstance(payload, int):
                msg_rcvd = True
        else:
            ts = payload.get("ts", datetime_empty)
            """
            if ts != 0 and last_update_time != 0:
                if ts >= last_update_time:
                    diff = ts - last_update_time
                else:
                    diff = last_update_time - ts
            if diff >= 3600:
                ts_corr = ts - diff
            else:
                ts_corr = ts
            """
            
            if not my_debug:
                print(TAG+f"received a MQTT message on topic: \"{topic}\"")
                #print(TAG+f"received a MQTT message on topic: \"{topic}\", timestamp: {ts}")
                #print(TAG+f"received a MQTT message on topic: \"{topic_rcvd}\", timestamp: {ts_corr}")
            if my_debug:
                print(TAG+f"msg: {msg.payload}")
        
    except Exception as e:
        print(TAG+"Unhandled exception:", str(e))

def convert_to_unix(dt):
    # dt: '2025-06-01T02:21:01'
    if dt == "unknown":
        return 0
    date_part, time_part = dt.split('T')
    year, month, day = map(int, date_part.split('-'))
    hour, minute, second = map(int, time_part.split(':'))

    # Adjust UTC+1 (subtract 1 hour)
    hour -= 1
    if hour < 0:
        hour += 24
        day -= 1  # Note: no month/year wraparound yet, keep simple

    tup = (year, month, day, hour, minute, second, 0, 0)  # No weekday or yearday
    timestamp = time.mktime(tup)
    if my_debug:
        print(f"[DEBUG] Unix timestamp = {timestamp}")
    return timestamp

def uxMinimum(yr1970: bool = True):
    if yr1970:
        return  0   #  = 1970-01-01, 1970 0:00:00 UTC
    else:
        return -2208988800 # = 1900-01-01 00:00:00 UTC

def uxMaximum():
    return 2147483647 # 2038-01-19 03:14:07 UTC (maximum value for a signed integer 32-bit number)

def convert_to_dtStr(uxTime):
    # print(f"convert_to_dtStr(): type(uxTimeS) = {type(uxTime)}")
    if not isinstance(uxTime, int):
        return datetime_empty
    if uxTime <= uxMinimum() or uxTime >= uxMaximum():  # max for 32-bit
        return datetime_empty
    # Convert to local time tuple
    t = time.gmtime(uxTime)  # do not use time.localtime() because we end up in portuguese time +1 hr (= Amsterdam hour!)
    # Format as ISO 8601 string: YYYY-MM-DDTHH:MM:SS
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
            t[0], t[1], t[2], t[3], t[4], t[5])

def split_msg():
    global topic_rcvd, payload, payloadLst, Publisher_ID, lightsColorIdx, lights_ON, lights_ON_old, lightsColorMax, lightsColorMin, globT, globP, globA, globH
    TAG = "split_msg(): "
    topic_found = False
    
    if topic_rcvd.startswith("$SYS"):
        return  # handle elsewhere
    
    try:
        topicIdx = -1
        for i in range(len(TOPIC_LST)):
            if topic_rcvd == TOPIC_LST[i]:
                topicIdx = i
                break
        if topicIdx >= 0:
            if my_debug:
                print(TAG+f"Topic rcvd: {topic_rcvd} found in TOPIC_LST: {TOPIC_LST[topicIdx]}")
            topic_found = True
        else:
            print(TAG+f"topic rcvd: {topic_rcvd} not in TOPIC_LST: {TOPIC_LST}")
        
        if not topic_found:
            return 
        
        doc = payload.get("doc", {})
        payloadLst = []
        datetime = datetime_empty
        # Step 1: Decode from bytes and parse JSON
        #decoded = json.loads(msg)
        if payload is None:
            print(TAG+"payload is None, skipping further processing.")
            return
        # Step 1.1: Check if the payload is empty
        if not payload:
            print(TAG+"Received an empty payload, skipping further processing.")
            return
        
        # Step 2: Pull shared metadata
        owner = payload.get("ow", "?")
        if owner == "unknown":
            Publisher_ID = PUBLISHER_ID  # if "unknown" we use the definition from secret.json
        elif owner == "Feath":
            Publisher_ID = "Feather"
        else:
            Publisher_ID = owner  # use the owner from the payload
            # Step 2: Pull shared metadata
        
        lbl_k = "ow"
        lbl_v = owner
        output = {lbl_k: lbl_v}
        payloadLst.append(output)
        
        description = payload.get("de", "unknown")
        lbl_k = "de"
        lbl_v = description
        output = {lbl_k: lbl_v}
        payloadLst.append(output)
        
        lbl_k = "dc"
        device_class = payload.get("dc", "unknown")
        if device_class == "BME280":
            lbl_v = device_class
        elif device_class == "home":
            lbl_v = device_class
        elif device_class == "colr":
            lbl_v = "color"
        else:
            lbl_v = device_class
        output = {lbl_k: lbl_v}
        payloadLst.append(output)
        
        lbl_k = "sc"
        state_class = payload.get("sc", "unknown") # == "measure":
        if state_class == "meas":
            state_class = "measurement"
        elif state_class == "inc":
            state_class = "incr"
        elif state_class == "dec":
            state_class = "decr"
        elif state_class == "ligh":
            state_class = "lights"
        else:
            state_class = "unknown"
 
        lbl_v = state_class
        output = {lbl_k: lbl_v}
        payloadLst.append(output)
        
        lbl_k = "vt"
        vt = payload.get("vt") # "vt" stands for value term
        if vt == "f":
            lbl_v = "float"
        elif vt == "i":
            lbl_v = "int"
        elif vt == "s":
            lbl_v = "str"
        elif vt == "b":
            lbl_v = "bool"
        output = {lbl_k: lbl_v}
        payloadLst.append(output)
        
        uxTime = payload.get("ts", "unknown")
        
        if uxTime <= uxMinimum() or uxTime >= uxMaximum(): # max for 32-bit
            uxTimeStr = "invalid"
        else:
            uxTimeStr = str(uxTime)
        
        if my_debug:
            print(TAG+f"uxTime = {uxTime}")
        if uxTime == 0:
            datetime = datetime_empty  # Default to 0 if unknown
        else: 
            datetime = convert_to_dtStr(uxTime)
            if my_debug:
                print(TAG+f"datetime = {datetime}")
        
        lbl_k = "tm" # NOTE: this label does not exist in the MQTT message (neither doc or reads)
        if datetime == "unknown" or datetime == datetime_empty:
            lbl_v = "--:--:--"
        else:
            time = datetime[-8:]
            lbl_v = time
        output = {lbl_k: lbl_v}
        payloadLst.append(output)
        
        lbl_k = "ts"
        lbl_v = uxTimeStr
        output = {lbl_k: lbl_v}
        payloadLst.append(output)
            
        if my_debug:
            ts = payload.get("ts", datetime_empty)
            print(TAG+f"Received msg from: {owner}, timestamp: {uxTime}") # was: "timestamp"

        # ✅ Make sure this matches your payload
        default_state_class = payload.get("sc", "unknown")  # 🆕 pulled from top-level
        if my_debug:
          print(TAG+f"owner: {owner} [{device_class}], timestamp: {uxTime}")
        
        if topicIdx == 0: # sensors/Feath/ambient
            # Step 3: Extract and flatten "reads"
            readings = payload.get("reads", {})

            for key, data in readings.items():
                label = key.upper()
                value = data.get("v", "??")
                unit = data.get("u", "")
                
                # min_val = data.get("mn", "?")
                # max_val = data.get("mx", "?")
                # sc = data.get("state_class", state_class)
                
                lbl_k = None
                lbl_v = None
                
                if label == "T":
                    t1 = "Temperature: "
                    globT = value # copy Temperature to global value (for use in draw())
                    lbl_k = "temp"
                    if vt == "f":
                        lbl_v = t1 + "{:4.1f} °C".format(value) # + str(value) + " °C"
                    elif vt == "i":
                        lbl_v = t1 + str(value) + " °C"
                    elif vt == "s":
                        lbl_v = t1 + value + " °C"
                elif label == "P":
                    t1 = "Pressure: "
                    globP = value # copy Pressure to global value (for use in draw())
                    lbl_k = "pres"
                    if vt == "f":
                        lbl_v = t1 + "{:6.1f} {:s}".format(value, unit)
                    elif vt == "i":
                        lbl_v = t1 + str(value) + unit
                    elif vt == "s":
                        lbl_v = t1 + value + unit
                elif label == "A":
                    t1 = "Altitude: "
                    globA = value # copy Altitude to global value (for use in draw())
                    lbl_k = "alti"
                    if vt == "f":
                        lbl_v = t1 + "{:5.1f} {:s}".format(value, unit)
                    elif vt == "i":
                        lbl_v = t1 + str(value) + unit
                    elif vt == "s":
                        lbl_v = t1 + value + unit
                elif label == "H":
                    t1 = "Humidity: "
                    globH = value # copy Humidity to global value (for use in draw())
                    lbl_k = "humi"
                    if vt == "f":
                        lbl_v = t1 + "{:5.1f} {:s}".format(value, unit)
                    elif vt == "i":
                        lbl_v = t1 + str(value) + unit
                    elif vt == "s":
                        lbl_v = t1 + value + unit
                output = {lbl_k: lbl_v}
                payloadLst.append(output)
            
            if my_debug:
                print(TAG+"Root fields:")
                print(TAG+f"owner:        {owner}")
                print(TAG+f"device_class: {device_class}")
                print(TAG+f"state_class:  {state_class}")
                print(TAG+f"msgID:        {uxTime}")
                print(TAG+"Reads fields")
                print(f"payloadLst: {payloadLst}")
        elif topicIdx == 1: # lights/Feath/toggle:
            """ 
            Example output of code below:
            split_msg(): toggle payload.keys() = dict_keys(['u', 'mx', 'mn', 'v'])
            split_msg(): toggle payload.items() = dict_items([('u', 'i'), ('mx', 0), ('mn', 1), ('v', 0)])
            split_msg():  key =  u, data =  i
            split_msg():  key = mx, data =  0
            split_msg():  key = mn, data =  1
            split_msg():  key =  v, data =  0
            """
            toggle_mx_val = None
            toggle_mn_val = None
            unit = None
            value = None
            toggle = payload.get("toggle", {})  # "toggle":{"v":0,"u":"i","mn":1,"mx":0}
            if not my_debug:
        
                print(TAG+f"toggle payload.keys() = {toggle.keys()}")
                print(TAG+f"toggle payload.items() = {toggle.items()}")
            for key, data in toggle.items():
                if not my_debug:
                    if isinstance(data, int):
                        print("{:s} key = {:>2s}, data = {:>2d}".format(TAG, key, data))
                    elif isinstance(data, str):
                        print("{:s} key = {:>2s}, data = {:>2s}".format(TAG, key, data))
                if key == "v": # value
                    value = data
                elif key == "u": # unit of measurement
                    unit = data
                elif key == "mx":
                    toggle_mx_val = data
                elif key == "mn":
                    toggle_mn_val = data

            if value is not None:
                # Check if, eventually, unit is "s" (String)
                if unit == "s":
                    value = int(value)
                lights_ON = True if value == 1 else False # set the global lights_ON flag
                if lights_ON != lights_ON_old:  # Only change if value differs from last received value
                    print(TAG+f"toggling ambient light neopixel leds {'on' if lights_ON == True else 'off'}")
                    #lights_ON_old = lights_ON
                else:
                    print(TAG+f"not toggling ambient light neopixel leds. lights_ON = {lights_ON}, lights_ON_old = {lights_ON_old}")
            else:
                print(TAG+f"value is: {value}")
        elif topicIdx in (2, 3):  # lights/Feath/color_inc or color_dec
            #if not lights_ON:
            #    return
            colorData = payload.get("colorInc") if topicIdx == 2 else payload.get("colorDec")
            if not my_debug:
                print(TAG + f"colorData payload.items() = {colorData.items()}")
            
            for key, data in colorData.items():
                if not my_debug:
                    if isinstance(data, int):
                        print(TAG + "key = {:>2s}, data = {:>2d}".format(key, data))
                    elif isinstance(data, str):
                        print(TAG + "key = {:>2s}, data = {:>2s}".format(key, data))

                if key == "v":  # value
                    value = data
                elif key == "u":  # unit of measurement
                    unit = data
                elif key == "mx":
                    lightsColorMax = data
                elif key == "mn":
                    lightsColorMin = data

            if value is not None:
                if unit == "s":
                    value = int(data)
                if my_debug:
                    print(TAG + f"value = {value}, lightsColorMin = {lightsColorMin}, lightsColorMax = {lightsColorMax}")
                
                if lightsColorMin <= value <= lightsColorMax:
                    lightsColorIdx = value
                    if my_debug:
                        print(TAG + f"lightsColorIdx set to: {lightsColorIdx}")
                else:
                    lightsColorIdx = -1
            else:
                lightsColorIdx = -1
                print(TAG+f"value is: {value}")
    except Exception as e:
        print(TAG+"error:", str(e))

def get_payload_member(key):
    global payloadLst, topic_idx
    TAG = "get_payload_member(): "
    if isinstance(payloadLst, list):
        if len(payloadLst) > 0:
            for entry in payloadLst:
                if my_debug:
                    print(TAG+f"entry: {entry}, payloadLst: {payloadLst}")
                if key in entry:
                    if my_debug:
                        print(TAG+f"key \'{key}\' found in entry {entry}")
                    return entry[key]
                else:
                    if my_debug:
                        print(TAG+f"key \'{key}\' not found in entry {entry}")
                        
    return ""  # if key not found


def draw(mode:int = 1):
    global lStart, paho_msg, payload_txt, payloadLst, msg_drawn, Publisher_ID, publisher_time, publisher_msgID, topic_idx, lights_ON, lights_ON_old
    TAG = "draw(): "
        
    if paho_msg is not None:
        if my_debug:
            print(TAG+f"paho_msg.topic = {paho_msg.topic}")
        if paho_msg.topic.startswith("$SYS"):
            return # handle elsewhere
    

    time_draw = "--:--:--" # Also used for setting the day or night text colour
    time_draw_hh = 0
    #if not msg_rcvd:
    #    print("draw(): no message received. Exiting this function...")
    #    return
    

    # Display the message
    # See: https://doc-tft-espi.readthedocs.io/tft_espi/colors/
    # NOTE: NAVY gives less brightness than ORANGE
    if time_draw != "--:--:--":
        time_draw_hh = int(time_draw[:2])
    else:
       time_draw_hh = 0
    hh = time_draw_hh    
    
    CURRENT_COLOUR = None
    
    if my_debug:
        print(TAG+f"hh = {hh}")
    
    #if  hh >= 9 and hh < 21:
    if  hh >= DISPLAY_HOUR_WAKEUP and hh < DISPLAY_HOUR_GOTOSLEEP:
        CURRENT_COLOUR = ORANGE
    else:
        CURRENT_COLOUR = NAVY
    x = 10
    y = 25
    line_space = 30
    margin = 10
    
    hdg = "MQTT " # pub : "

    if have_ip(False):
        if lStart:
            print("Network OK")
    if mqtt_connected:
        if lStart:
            print("MQTT OK")

    if msg_rcvd:
        lStart = False

        time_draw = get_payload_member("tm")
        if my_debug:
            print(TAG+f"time_draw = {time_draw}")
        if time_draw != "--:--:--":
            time_draw_hh = int(time_draw[:2])
        else:
           time_draw_hh = 0
        hh = time_draw_hh    
        if  hh >= DISPLAY_HOUR_WAKEUP and hh < DISPLAY_HOUR_GOTOSLEEP:
            CURRENT_COLOUR = ORANGE
        else:
            CURRENT_COLOUR = NAVY
    
    y += line_space
    
    if mode == 0:
        # Word wrapping logic
        words = payload_txt.split()  # Split the message into words
        current_line = ""  # Start with an empty line
        
        for word in words:
            test_line = current_line + (word + " ")
            line_width = len(test_line)

            if line_width > WIDTH - margin:
                print(current_line.strip())
                y += line_space
                current_line = word + " "  # Start a new line with the current word
            else:
                current_line = test_line

        if current_line:
            print(current_line.strip())
        
        y += line_space
            
    elif mode == 1: # do the PaulskPt method
        #                                             Examples:
        # Read the "doc" members
        time_draw = get_payload_member("tm")      # → "--:--:--"
        ow_draw = Publisher_ID                    # get_payload_member("ow")  # → "Feather" or "UnoR4W"
        de_draw = get_payload_member("de")        # → "PC-Lab"
        dc_draw = get_payload_member("dc")        # → "BME280", "home", "colr", "colr"
        # sc_draw = get_payload_member("sc");     # → "meas", "ligh", "inc", "dec"
        timestamp_draw = get_payload_member("ts") # → "1748945128" = Tue Jun 03 2025 10:05:28 GMT+0000
        
        if topic_idx == 0:
            temp_draw = get_payload_member("temp")    # → "Temperature: 30.3 °C"
            pres_draw = get_payload_member("pres")    # → "Pressure: 1002.1 rHa"
            alti_draw = get_payload_member("alti")    # → "Altitude: 93.3m"
            humi_draw = get_payload_member("humi")    # → "Humidity: 42.2 %rH"
            # print(TAG+f"type(temp_draw) = {type(temp_draw)}, type(pres_draw) = {type(pres_draw)}, type(humi_draw= {type(humi_draw)}")
        elif topic_idx == 1:
            toggle_draw1 = "lights_ON = {:s},".format("Yes" if lights_ON else "No") #  get_payload_member("v")
            toggle_draw2 = "lights_ON_old = {:s}".format("Yes" if lights_ON_old else "No")
            if lights_ON != lights_ON_old:
                lights_ON_old = lights_ON
            if not my_debug:
                print(TAG+f"toggle_draw1 = {toggle_draw1}")
                print(TAG+f"toggle_draw2 = {toggle_draw2}")
        elif topic_idx in (2,3):
            color_txt1_draw = "lightsColorIdx = {:d}".format(lightsColorIdx)
            if lightsColorIdx in blColorNamesDict.keys():
                color_txt2_draw = blColorNamesDict[lightsColorIdx]
            else:
                color_txt2_draw = ""
            if topic_idx == 2:
                t2 = "inc"
            elif topic_idx == 3:
                t2 = "dec"
            if not my_debug:
                print(TAG+f"color_txt1_draw = \"{color_txt1_draw}\"")
                print(TAG+f"color_txt2_draw = \"{color_txt2_draw}\"")
        else:
            return # No valid topic_idx
        
        my_scale = 2
        y = 25 # restart y position

        print(f"{hdg} {time_draw}")
        print(f"{ow_draw} {de_draw} {dc_draw}")
        print(f"msgID: {timestamp_draw}")
        if my_debug:
            print(TAG+f"topic_idx: {topic_idx} = topic: \"{TOPIC_LST[topic_idx]}\"")
        if topic_idx == 0: # sensors/Feath/ambient
            print(f"{temp_draw}")
            print(f"{pres_draw}")
            print(f"{alti_draw}")
            print(f"{humi_draw}")
            #if  hh >= DISPLAY_HOUR_WAKEUP and hh < DISPLAY_HOUR_GOTOSLEEP:
            if use_sense_hat:
                t = round(globT, 1)
                p = round(globP, 1)
                h = round(globH, 1)
                a = round(globA, 2)
                #if t > 18.3 and t < 26.7:
                txt_colour_soft_white = [64, 64, 64]
                bg_soft_green         = [ 0, 64,  0]
                bg_soft_red           = [64,  0,  0]
                if t > 18.3 and t < 26.9:
                    bg = bg_soft_green  # green
                else:
                    bg = bg_soft_red  # red
                
                
                if use_sense_hat_data:
                    get_sensehat_data()
                    avgT = round((t + senseHatT) / 2, 2)
                    avgP = round((p + senseHatP) / 2, 2)
                    avgH = round((h + senseHatH) / 2, 2)
                    t1 = "temp: "
                    p1 = "pres: "
                    h1 = "humi: "
                    ext_sensor_data_txt = "{:s}{:6.2f}, {:s}{:7.2f}, {:s}{:6.2f}, alti: {:6.2f}".format(t1, t, p1, p, h1, h, a)
                    sensehat_data_txt   = "{:s}{:6.2f}, {:s}{:7.2f}, {:s}{:6.2f}".format(t1, senseHatT, p1, senseHatP, h1, senseHatH)
                    avg_data_txt        = "{:s}{:6.2f}, {:s}{:7.2f}, {:s}{:6.2f}".format(t1, avgT, p1, avgP, h1, avgH)
                    spc26 = 26 * "."
                    spc32 = 32 * "."
                    if not my_debug:
                        print(f"Ext MQTT tph sensor data{spc26}: {ext_sensor_data_txt}")
                        print(f"Sense HAT tph data{spc32}: {sensehat_data_txt}")
                        print(f"Average of ext tph sensor and sense hat tph sensor: {avg_data_txt}")
                if  hh >= DISPLAY_HOUR_WAKEUP and hh < DISPLAY_HOUR_GOTOSLEEP:             
                    if use_average:
                        msg = f"AVG Temp={avgT}, Pres={avgP}, Humi={avgH}"
                    else:
                        msg = f"Temp={t}, Pres={p}, Humi={h}"   
                    # Displaying the scrolling text takes about 28 seconds with this scroll_speed 
                    sense.show_message(msg, scroll_speed=0.10, text_colour = txt_colour_soft_white, back_colour=bg)
                    clr_sense_hat()
                else:
                    print(TAG+"it is night. We\'re not showing data on the LED matrix of the sense hat")
        elif topic_idx == 1: # lights/Feath/toggle
            print(f"{toggle_draw1}")
            print(f"{toggle_draw2}")
        elif topic_idx in (2,3): # lights/Feath/color_inc or lights/Feath/color_dec
            print(f"{color_txt1_draw}")
            print(f"{color_txt2_draw}")
    
    msg_drawn = True
    
    if not my_debug:
        do_line(107)

def print_file_contents(tag, file_path, file_label):
    try:
        file_size = os.stat(file_path)[6]
        if file_size > 0:
            print(f"Size of {file_label}: {file_size}.")
            print(f"Contents of {file_label}: \"{file_path}\"")
            with open(file_path, 'r') as file_obj:
                for i, line in enumerate(file_obj, start=1):
                    print(f"{tag} {i:02d}) {line.strip()}")
            do_line()
        else:
            print(tag + f"{file_label} \"{file_path}\" is empty")
    except OSError as e:
        print(tag + f"{file_label} not found or unable to open. Error: {e}")
        
def pr_log():
    global log_path, log_obj, log_size_max
    TAG = "pr_log(): "
    sys_broker_path = "/sys_broker.json" # get_prefix() + "sys_broker.json"

    # Print sys_broker.json contents
    print_file_contents(TAG, sys_broker_path, "sys_broker json file")

    # Close log object if open
    if log_obj:
        log_obj.close()

    # Print log file contents
    print_file_contents(TAG, log_path, "log file")


def cleanup():
    global ref_exist, ref_obj, ref_path, log_exist, log_obj, log_path
    if ref_obj: # and ref_path is not None and ref_exist:
        ref_obj.close()
    if log_obj: # and log_path is not None and log_exist:
        log_obj.close()

def setup():
    global client, mqttc, CLIENT_ID, BROKER, PORT, TOPIC0, TOPIC1, TOPIC2, TOPIC3, msg_drawn, mqtt_connected, lights_ON, lights_ON_old
    # MQTT client setup
    TAG = "setup(): "
    """
    if not ck_log(err_log_fn):  # Check if the error log file exists
        print(TAG+f"Error log file: \"{err_log_fn}\" does not exist, creating it")
        create_err_log_file()
    """
    if use_sense_hat:
        clr_sense_hat()
    
    # print(TAG+"Switching ambient light neopixel leds off")
    lights_ON = False
    lights_ON_old = False
  
    #rx_bfr=1024  # ← Increase to 1024 or higher
    #print(TAG+f"Connecting to MQTT broker at {BROKER} on port {PORT}") # , recv_buffer {rx_bfr}")
    print(TAG, end='')
    print("connecting to MQTT ", end='')
    broker_typ = "local" if use_local_broker == True else "external"
    print(f"{broker_typ} broker on port {PORT}")
    
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subscribe

    if delete_logs:
        del_logfiles() # for test
    else:
        print(TAG, end='')
        print("not deleting log files, flag: \"delete_logs\" = ", end='')
        del_flg = "True" if delete_logs == True else "False"
        print(f"{del_flg}")
    try:
        # client.connect()
        mqttc.connect(BROKER, PORT, 60)
        mqtt_connected = True
        print(TAG+f"successfully connected to MQTT broker") # at {BROKER}.")
        add_to_log("connected to MQTT broker: {}".format(BROKER))
        for i in range(len(TOPIC_LST)):
            mqttc.subscribe(TOPIC_LST[i])
            #print(TAG+f"Subscribed to topic: \"{TOPIC_LST[i].decode()}\"")
            print(TAG+f"subscribed to topic: \"{TOPIC_LST[i]}\"")
            #add_to_log("subscribed to topic: {}".format(TOPIC_LST[i].decode()))
            add_to_log("subscribed to topic: {}".format(TOPIC_LST[i]))
        msg_drawn = False
    
    except Exception as e:
        if e.args[0] == 113: # EHOSTUNREACH
            t = f"failed to reach the host with address: {BROKER} and port: {PORT}"
            print(TAG+f"{t}")
            add_to_log(t)
            mqtt_connected = False
        else:
            print(TAG+f"failed to connect to MQTT broker: {e}")
            mqtt_connected = False
    except KeyboardInterrupt as e:
        print(TAG+f"keyboardInterrupt. Exiting...\n")
        add_to_log("session interrupted by user — logging and exiting.")
        cleanup()
        pr_ref()
        pr_log()
        raise

# Here begins the "loop()" part:
# def main():
# global client, msg_rcvd, last_update_time, publisher_msgID
# for compatibility with the Presto "system" the line "def main()" and below it the "globals" line have been removed
rotate_log_if_needed() # check if we need to create a new log file
list_logfiles()
setup()
draw(0) # Ensure the default message "Waiting for Messages..." is displayed
TAG = "loop(): "
start_t = time.time()
current_t = start_t
elapsed_t = 0
interval_t = 5 * 60  # Interval to check for call rotate_log_if_needed() in seconds (300 seconds = 5 minutes)

save_broker_dict_interval_t = 15 * 60 # 15 minutes
save_broker_dict_start_t = 0
save_broker_dict_curr_t = 0
save_broker_dict_elapsed_t = 0

msg_rx_timeout_interval_t = 3 * 60 # 3 minutes
msg_rx_timeout_start_t = start_t # same as start_t
msg_rx_timeout_curr_t = 0
msg_rx_timeout_elapsed_t = 0
msg_rx_timeout = False
last_triggered = -1
show_size = True  # Show the size of the current log file

# mqttc.loop.forever()
mqttc.loop_start()

while True:
    try:
        current_t = time.time()
        elapsed_t = current_t - start_t
        
        save_broker_dict_elapsed_t = save_broker_dict_curr_t - save_broker_dict_start_t
        if save_broker_dict_elapsed_t >= save_broker_dict_interval_t:
            save_broker_dict_start_t = save_broker_dict_curr_t
            save_broker_dict()
            
        if my_debug:
            if elapsed_t % 10 == 0 and (elapsed_t != last_triggered or last_triggered == -1):
                last_triggered = elapsed_t
                print(TAG+f"elapsed_t = {elapsed_t:.2f} seconds")
                # print(TAG+f"current_t = {current_t}, start_t = {start_t}, elapsed_t = {elapsed_t:.2f} seconds")
        if elapsed_t >= interval_t:
            start_t = current_t  # Reset the start time
            # Check if we need to create a new log file
            # and show the size of the current log file
            rotate_log_if_needed(show=show_size)
            show_size = not show_size  # Toggle the display of the log file size  
        
        # Wait for MQTT messages (non-blocking check)
        while True:
            msg_rx_timeout_current_t = time.time()

            if msg_rcvd:
                mqtt_callback(topic, paho_msg)
                msg_rx_timeout_start_t = msg_rx_timeout_current_t # update the start time
                break
           
            msg_rx_timeout_elapsed_t = msg_rx_timeout_current_t - msg_rx_timeout_start_t
            if msg_rx_timeout_elapsed_t >= msg_rx_timeout_interval_t:
                msg_rx_timeout_start_t = msg_rx_timeout_current_t
                msg_rx_timeout = True
                break
        
        if msg_rx_timeout:
            msg_rx_timeout = False # reset flag
            print(TAG+"msg rx timedout!")
            continue # loop

        # Refresh the display periodically
        if msg_rcvd:
            split_msg()
            if my_debug:
                if publisher_msgID:
                    print(f"{TAG}MQTT message received from: {publisher_msgID}")
                else:
                    print(f"{TAG}MQTT message received")

            draw(1) # Display the new message in mode "PaulskPt"
            msg_rcvd = False
        elif time.time() - last_update_time > MESSAGE_DISPLAY_DURATION:
            draw(1)  # Refresh the screen with the current message
            last_update_time = abs(time.time())
        if msg_rcvd:
            # Cleanup
            print(TAG+"Cleaning up:")
            msg_rcvd = False # reset this flag

    except Exception as e:

        mqttc.loop_stop()
        if e.args[0] == 103:
            print(TAG+f"Error ECONNABORTED") # = Software caused connection abort
            # add_to_log(e)
            print(TAG+f"Reconnecting to MQTT broker...")
            setup()
            #raise RuntimeError
        elif e.args[0] == 104: # ECONNRESET
            print(TAG+f"Error ECONNRESET") # = Software caused connection abort
            # sys.print_exception(e)
            #add_to_log(e)
            print(TAG+f"Reconnecting to MQTT broker...")
            setup()
        else:
            print("loop(): Error:", repr(e))
            #err_txt = f"Error while waiting for MQTT messages:"
            #if my_debug:
            #    print(TAG+f"{err_txt} {e}")
            #else:
            #    print(TAG+f"{err_txt} {e.__class__.__name__}: {e}")
            cleanup()        
            raise RuntimeError
    except KeyboardInterrupt as e:
        print(TAG+f"KeyboardInterrupt: exiting...\n")
        # sys.print_exception(e)
        #   err.log(e)
        if use_sense_hat:
            clr_sense_hat()
        mqttc.loop_stop()
        add_to_log("Session interrupted by user — logging and exiting.")
        save_broker_dict()
        cleanup()
        pr_ref()
        pr_log()
        raise

# for compatibility with the Presto "system" the next two lines have been commented out
# if __name__ == '__main__':
#   main()
