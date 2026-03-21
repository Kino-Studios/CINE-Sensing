from setuptools import find_packages, setup

package_name = 'imu_publisher'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/gyroscope_publish.py',
            'launch/vio_publisher.py',
            'launch/imu_publisher_launch.py',
            'launch/imu_bridge.py',
            'launch/imu_bridge_launch.py',
            'launch/start_mavros.sh'
        ]),
        ('share/' + package_name + '/config', ['config/comms.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@users.noreply.github.com',
    description='Flight controller data processing and VIO integration package',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gyroscope_publisher = imu_publisher.gyroscope_publish:main',
            'vio_publisher = imu_publisher.vio_publisher:main',
            'imu_bridge = imu_publisher.imu_bridge:main',
            'imu_checker = imu_publisher.imu_checker:main',
        ],
    },
)
