from glob import glob
from pathlib import Path

from setuptools import find_packages, setup

package_name = 'cine_sensing_config'

profile_data_files = [
    (
        f'share/{package_name}/config/profiles/{Path(profile_directory).name}',
        glob(f'{profile_directory}/*.json'),
    )
    for profile_directory in sorted(glob('config/profiles/*'))
]

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.json')),
        *profile_data_files,
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
