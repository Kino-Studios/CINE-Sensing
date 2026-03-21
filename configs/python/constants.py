class ModelDetectionConstants:
    MODEL_PATH = '/workspace/sensing_ws/src/yolo_detection/models/homeobjects_yolo11n_trained.pt'

    CAMERA_IMAGE_TOPIC = '/camera/image_raw'
    BOUNDING_BOX_TOPIC = '/object_detection/bounding_box'

    IMAGE_ENCODING = 'bgr8'
    IMAGE_DIR = '~/object_detection_images'

    OBB_COORDS_LENGTH = 8
    NUM_BOUNDING_BOX_POINTS = 4

    QOS_DEPTH = 10
    QOS_RELIABILITY = 'RELIABLE'
    QOS_DURABILITY = 'VOLATILE'
    QOS_HISTORY = 'KEEP_LAST'

    CONFIDENCE_THRESHOLD = 0.25
    IOU_THRESHOLD = 0.4

class UserRequestedParameters:
    # for the user object, its the ids of the objects that the model uses (ill make it a chair for now)
    USER_OBJECT_ID = 2

class RuleOfThirdsConstants:
    FRAME_WIDTH = 1152
    FRAME_HEIGHT = 648

    GRID_LINE_1_X = FRAME_WIDTH / 3.0
    GRID_LINE_2_X = 2 * FRAME_WIDTH / 3.0
    GRID_LINE_1_Y = FRAME_HEIGHT / 3.0
    GRID_LINE_2_Y = 2 * FRAME_HEIGHT / 3.0

    ANCHOR_POINTS = [
        (GRID_LINE_1_X, GRID_LINE_1_Y),
        (GRID_LINE_2_X, GRID_LINE_1_Y),
        (FRAME_WIDTH, GRID_LINE_1_Y),
        (GRID_LINE_1_X, GRID_LINE_2_Y),
        (GRID_LINE_2_X, GRID_LINE_2_Y),
        (FRAME_WIDTH, GRID_LINE_2_Y),
        (GRID_LINE_1_X, FRAME_HEIGHT),
        (GRID_LINE_2_X, FRAME_HEIGHT),
        (FRAME_WIDTH, FRAME_HEIGHT),
    ]

    CORE_ANCHOR_POINTS = [
        (GRID_LINE_1_X, GRID_LINE_1_Y),
        (GRID_LINE_2_X, GRID_LINE_1_Y),
        (GRID_LINE_1_X, GRID_LINE_2_Y),
        (GRID_LINE_2_X, GRID_LINE_2_Y),
    ]
