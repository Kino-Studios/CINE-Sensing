from setuptools import find_packages, setup

package_name = 'cine_sensing_setpoint'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@users.noreply.github.com',
    description=(
        'Forwards cinematography position, velocity, acceleration and attitude setpoints to MAVROS setpoint topics.'
    ),
    license='GPL-3.0-only',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'mavros_setpoints = cine_sensing_setpoint.mavros_setpoints:main',
        ],
    },
)
