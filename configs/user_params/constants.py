class ModelDetectionConstants:
    MODEL_PATH = '/home/fishnos/bspline-cinematography-generator-research/training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt'
    
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
