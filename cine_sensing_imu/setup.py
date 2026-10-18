from glob import glob

from setuptools import find_packages, setup

package_name = 'cine_sensing_imu'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            'share/' + package_name + '/launch',
            [*glob('launch/*.launch.py'), 'launch/start_mavros.sh'],
        ),
        ('share/' + package_name + '/config', glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@users.noreply.github.com',
    description=(
        'Republishes MAVROS IMU data for VINS-Fusion, extracts gyroscope rates, and republishes VINS odometry as VIO pose.'
    ),
    license='GPL-3.0-only',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'gyroscope_publisher = cine_sensing_imu.gyroscope_publish:main',
            'vio_publisher = cine_sensing_imu.vio_publisher:main',
            'imu_bridge = cine_sensing_imu.imu_bridge:main',
            'imu_checker = cine_sensing_imu.imu_checker:main',
        ],
    },
)
