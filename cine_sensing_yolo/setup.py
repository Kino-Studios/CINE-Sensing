from glob import glob

from setuptools import find_packages, setup

package_name = 'cine_sensing_yolo'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/models', glob('models/*.pt')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@users.noreply.github.com',
    description=(
        'Runs a YOLO detector on camera frames and publishes the tracked subject bounding box, size and centre.'
    ),
    license='GPL-3.0-only',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'bb_extractor = cine_sensing_yolo.bb_extractor:main',
            'yolo_camera = cine_sensing_yolo.yolo_camera:main',
        ],
    },
)
