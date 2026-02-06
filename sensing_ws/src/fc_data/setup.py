from setuptools import find_packages, setup

package_name = 'fc_data'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/gyroscope_publish.py',
            'launch/vio_publisher.py',
            'launch/fc_data_launch.py',
            'launch/imu_bridge.py',
            'launch/imu_bridge_launch.py',
            'launch/start_mavros.sh'
        ]),
        ('share/' + package_name + '/config', ['../../../configs/gyroscope/comms.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@cine-sensing.dev',
    description='Flight controller data processing and VIO integration package',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gyroscope_publisher = fc_data.gyroscope_publish:main',
            'vio_publisher = fc_data.vio_publisher:main',
            'imu_bridge = fc_data.imu_bridge:main',
            'imu_checker = fc_data.imu_checker:main',
        ],
    },
)
