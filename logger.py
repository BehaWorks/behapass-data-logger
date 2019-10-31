import json
import uuid
from pprint import pprint

import openvr
import swagger_client
import time
from swagger_client.rest import ApiException

import triad_openvr as vr

config = None

try:
    with open('config/config.json', 'r') as file:
        config = json.load(file)
except FileNotFoundError:
    print('Could not load config.json.')

sid_length = config['sid_length']
sampling_rate = config['sample_rate']
api_host = config['api_host']
button = config['button']
button_options = config['button_options']
if button not in button_options:
    print("Button " + button + "not supported. Using trigger.")
    button = 'trigger'
    print("Supported buttons: " + button_options)


def transform_movements(data, sid, controller):
    rtn = []

    for timestamp, x, y, z, yaw, pitch, roll, r_x, r_y, r_z in zip(data["time"], data['x'], data['y'], data['z'],
                                                                   data['yaw'], data['pitch'], data['roll'],
                                                                   data['r_x'], data['r_y'], data['r_z']):
        rtn.append({
            "session_id": sid,
            "timestamp": timestamp,
            "controller_id": controller,
            "x": x,
            "y": y,
            "z": z,
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "r_x": r_x,
            "r_y": r_y,
            "r_z": r_z
        })

    return rtn


def recording_device(devices):
    for d in devices:
        if d.get_controller_inputs()[button] > 0:
            return d

    return None


def is_recording(d):
    return d.get_controller_inputs()[button] > 0


def sample(vr_device, num_samples, sample_rate, session_id):
    interval = 1 / sample_rate
    poses = vr.pose_sample_buffer()
    input_states = []
    sample_start = time.time()
    i = 0
    while is_recording(vr_device):
        start = time.time()
        pose = vr.get_pose(vr_device.vr)
        poses.append(pose[vr_device.index].mDeviceToAbsoluteTracking, time.time() - sample_start)
        input_states.append(vr_device.get_controller_inputs())
        input_states[i]['timestamp'] = time.time() - sample_start
        input_states[i]['session_id'] = session_id
        input_states[i]['controller_id'] = controller_serial
        i += 1
        sleep_time = interval - (time.time() - start)
        if sleep_time > 0:
            time.sleep(sleep_time)
    return poses, input_states


sid = uuid.uuid4().hex[0:sid_length]
device = None
try:
    v = vr.triad_openvr()

    print("Finding controllers...")
    controllers = []
    for object_name in v.object_names['Controller']:
        controllers.append(v.devices[object_name])
    if len(controllers) is 0:
        print('No controller found. Exiting.')
        exit(2)

    print('Waiting for input... Press recording button to start recording movement. Release to stop.')
    while device is None:
        time.sleep(0.1)
        device = recording_device(controllers)

    controller_serial = device.get_serial()
    print("Recording movement on controller " + controller_serial)
    data, buttons = sample(device, 150, sampling_rate, sid)
    print("Recording stopped")
    movements = transform_movements(data.__dict__, sid, controller_serial)
except openvr.error_code.InitError_Init_HmdNotFoundPresenceFailed:
    print('VR initialisation error (is HMD connected and SteamVR running?), using example data...')
    f = open('example_movements.json', 'r')
    data = json.load(f)
    movements = transform_movements(data, "TEST_SESSION", "EXAMPLE")
    f = open("example_buttons.json", "r")
    buttons = json.load(f)
    f.close()

api_client = swagger_client.LoggerApi()

f = open("vr_data.json", "w")
json.dump(data.__dict__, f)
f.close()
f = open("buttons.json", "w")
json.dump(buttons, f)
f.close()

pprint(movements)

try:
    api_client.api_client.configuration.host = api_host
    api_response = api_client.post_logger_record(payload={"movements": movements, "buttons": buttons})
    pprint(api_response)
except ApiException as e:
    print("Exception when calling LoggerApi->post_logger_record: %s\n" % e)
