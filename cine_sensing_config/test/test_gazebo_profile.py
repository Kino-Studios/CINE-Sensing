import json
from pathlib import Path

CONFIG_DIRECTORY = Path(__file__).resolve().parents[1] / 'config'
GAZEBO_PROFILE_DIRECTORY = CONFIG_DIRECTORY / 'profiles' / 'gazebo'
CHANGED_VINS_KEYS = {'body_T_cam0', 'estimate_extrinsic'}


def load_json(path):
    return json.loads(path.read_text())


def test_gazebo_vins_matches_base_except_simulator_keys():
    base = load_json(CONFIG_DIRECTORY / 'vins.json')['vins_config']
    gazebo = load_json(GAZEBO_PROFILE_DIRECTORY / 'vins.json')['vins_config']

    assert {key: value for key, value in base.items() if key not in CHANGED_VINS_KEYS} == {
        key: value for key, value in gazebo.items() if key not in CHANGED_VINS_KEYS
    }


def test_gazebo_vins_mounts_the_camera_forward_of_the_body_without_estimating_it():
    gazebo = load_json(GAZEBO_PROFILE_DIRECTORY / 'vins.json')['vins_config']

    assert gazebo['estimate_extrinsic'] == 0
    assert gazebo['body_T_cam0']['data'] == [0, 0, 1, 0.05, -1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1]


def test_gazebo_camera_matches_simulated_lens():
    camera = load_json(GAZEBO_PROFILE_DIRECTORY / 'vins_camera.json')

    assert camera['model_type'] == 'PINHOLE'
    assert (camera['image_width'], camera['image_height']) == (1152, 648)
    assert camera['projection_parameters'] == {
        'fx': 497.5985575,
        'fy': 497.5985575,
        'cx': 576.0,
        'cy': 324.0,
    }
    assert camera['distortion_parameters'] == {
        'k1': -0.0578246072,
        'k2': -0.0328310705,
        'p1': -0.00243136122,
        'p2': 0.000290213152,
    }


def test_gazebo_yolo_reads_the_bridged_image():
    params = load_json(GAZEBO_PROFILE_DIRECTORY / 'user_params.json')

    assert params['ModelDetectionConstants']['CAMERA_IMAGE_TOPIC'] == '/camera/image_raw'


def test_gazebo_yolo_loads_the_pinned_yolov8n_weights():
    params = load_json(GAZEBO_PROFILE_DIRECTORY / 'user_params.json')

    # A bare file name: the Gazebo launch runs the detector in the weights directory, where
    # the image's fetch_weights.py leaves the hash-checked yolov8n.pt.
    assert params['ModelDetectionConstants']['MODEL_PATH'] == 'yolov8n.pt'


def test_gazebo_yolo_keeps_person_detections():
    params = load_json(GAZEBO_PROFILE_DIRECTORY / 'user_params.json')

    assert params['UserRequestedParameters']['USER_OBJECT_ID'] == 0


def test_gazebo_user_params_match_base_except_image_topic_model_object_id_and_note():
    base = load_json(CONFIG_DIRECTORY / 'user_params.json')
    gazebo = load_json(GAZEBO_PROFILE_DIRECTORY / 'user_params.json')
    base.pop('_note')
    gazebo.pop('_note')
    base['ModelDetectionConstants'].pop('CAMERA_IMAGE_TOPIC')
    gazebo['ModelDetectionConstants'].pop('CAMERA_IMAGE_TOPIC')
    base['ModelDetectionConstants'].pop('MODEL_PATH')
    gazebo['ModelDetectionConstants'].pop('MODEL_PATH')
    base['UserRequestedParameters'].pop('USER_OBJECT_ID')
    gazebo['UserRequestedParameters'].pop('USER_OBJECT_ID')

    assert gazebo == base
