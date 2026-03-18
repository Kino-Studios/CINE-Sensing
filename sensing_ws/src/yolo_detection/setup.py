from setuptools import find_packages, setup

package_name = 'yolo_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Daniel Kosukhin',
    maintainer_email='180136815+fishnos@users.noreply.github.com',
    description='YOLO object detection node and inference scripts',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'bb_extractor = yolo_detection.bb_extractor:main',
        ],
    },
)
