from glob import glob

from setuptools import find_packages, setup

package_name = 'cine_sensing_camera'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@users.noreply.github.com',
    description=(
        'Publishes grayscale frames from a Raspberry Pi Camera Module 3 (rpicam or OpenCV capture) for VIO and detection.'
    ),
    license='GPL-3.0-only',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'camera_publisher = cine_sensing_camera.camera_publisher:main',
            'feature_viewer = cine_sensing_camera.feature_viewer:main',
        ],
    },
)
