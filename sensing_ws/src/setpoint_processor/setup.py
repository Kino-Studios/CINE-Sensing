from setuptools import find_packages, setup

package_name = 'setpoint_processor'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@cine-sensing.dev',
    description='Bridges cinematography setpoints to MAVROS',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mavros_setpoints = setpoint_processor.mavros_setpoints:main',
        ],
    },
)
