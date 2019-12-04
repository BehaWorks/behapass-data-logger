import json
import uuid
from pprint import pprint

import openvr
import swagger_client
import time
from datetime import datetime
from swagger_client.rest import ApiException

import triad_openvr as vr

HEADSET, CONTROLLER_1, CONTROLLER_2 = "hmd", "controller-1", "controller-2"

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


def transform_movements(data, sid, device_id, user_id):
    rtn = []

    for timestamp, x, y, z, yaw, pitch, roll, r_x, r_y, r_z in zip(data["time"], data['x'], data['y'], data['z'],
                                                                   data['yaw'], data['pitch'], data['roll'],
                                                                   data['r_x'], data['r_y'], data['r_z']):

        dict = {"session_id": sid}
        if user_id is not None:
            dict.update({"user_id": user_id})
        dict.update({
            "session_id": sid,
            "timestamp": timestamp,
            "controller_id": device_id,
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
        rtn.append(dict)

    return rtn


def recording_device(devices):
    for d in devices:
        if d.get_controller_inputs()[button] > 0:
            return d

    return None


def is_recording(d):
    return d.get_controller_inputs()[button] > 0

def sample(controller, hmd, num_samples, sample_rate, session_id, user_id):
    interval = 1 / sample_rate
    hmd_poses = vr.pose_sample_buffer()
    controller_poses = vr.pose_sample_buffer()
    input_states = []
    sample_start = time.time()
    i = 0
    while is_recording(controller):
        start = time.time()

        controller_pose = vr.get_pose(controller.vr)
        controller_poses.append(controller_pose[controller.index].mDeviceToAbsoluteTracking, time.time() - sample_start)

        hmd_pose = vr.get_pose(hmd.vr)
        hmd_poses.append(hmd_pose[hmd.index].mDeviceToAbsoluteTracking, time.time() - sample_start)

        input_states.append(controller.get_controller_inputs())
        input_states[i]['timestamp'] = time.time() - sample_start
        input_states[i]['session_id'] = session_id
        input_states[i]['controller_id'] = controller_serial
        if user_id is not None:
            input_states[i]['user_id'] = user_id
        i += 1
        sleep_time = interval - (time.time() - start)
        if sleep_time > 0:
            time.sleep(sleep_time)
    return controller_poses, hmd_poses, input_states


def post_record(api_client, controller_movements, hmd_movements, buttons):
    try:
        api_response = api_client.post_logger_record(payload={"movements": controller_movements + hmd_movements, "buttons": buttons})
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling LoggerApi->post_logger_record: %s\n" % e)


api_client = swagger_client.LoggerApi()
api_client.api_client.configuration.host = api_host

try:
    v = vr.triad_openvr()

    print("Finding controllers...")
    controllers = []
    hmd = None
    for object_name in v.object_names['Controller']:
        controllers.append(v.devices[object_name])
    if len(controllers) is 0:
        print('No controller found. Exiting.')
        exit(2)
    for object_name in v.object_names['HMD']:
        hmd = v.devices[object_name]

    user = None
    response = input('Do you wish to label logged data with a specific user? [y/n]')
    if response == 'y':
        user = input('Type the name of user: ')

    print('Logger ready. Press recording button to start recording movement. Release to stop.')
    i = 1

    while True:
        # time.sleep(0.1)
        controller = recording_device(controllers)

        if controller is not None:
            sid = str(datetime.now().strftime("%Y/%m/%d-%H:%M:%S-")) + uuid.uuid4().hex[0:sid_length]
            controller_serial = controller.get_serial()
            print("Recording movement on controller " + controller_serial)
            hmd_serial = hmd.get_serial()
            print("Recording movement on HMD " + hmd_serial)
            try:
                controller_data, hmd_data, buttons = sample(controller, hmd, 150, sampling_rate, sid, user)
                print("Recording stopped")
                controller_movements = transform_movements(controller_data.__dict__, sid, CONTROLLER_1, user)
                hmd_movements = transform_movements(hmd_data.__dict__, sid, HEADSET, user)

                post_record(api_client, controller_movements, hmd_movements, buttons)
                print(i)
                i = i + 1
            except ZeroDivisionError:
                print("Float division by zero")
                controller2 = recording_device(controllers)

                while is_recording(controller):
                    pass

except openvr.error_code.InitError_Init_HmdNotFoundPresenceFailed:
    print('VR initialisation error (is HMD connected and SteamVR running?), using example data...')
    f = open('data/example_movements.json', 'r')
    data = json.load(f)
    movements = transform_movements(data, "TEST_SESSION", "EXAMPLE", None)
    f = open("data/example_buttons.json", "r")
    buttons = json.load(f)
    f.close()

print(movements)
post_record(api_client, movements, buttons)
