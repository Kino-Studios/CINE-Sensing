from glob import glob

from setuptools import find_packages, setup

package_name = 'cine_sensing_config'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.json')),
        ('share/' + package_name + '/config/gyroscope', glob('config/gyroscope/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@users.noreply.github.com',
    description=(
        'Shared JSON configuration for the CINE-Sensing camera, IMU, YOLO and VIO nodes, '
        'with a Python loader that finds it in the install space.'
    ),
    license='GPL-3.0-only',
    extras_require={'test': ['pytest']},
)
