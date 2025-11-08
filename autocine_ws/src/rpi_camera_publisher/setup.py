from setuptools import find_packages, setup

package_name = 'rpi_camera_publisher'

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
    maintainer='Your Name',
    maintainer_email='your_email@example.com',
    description='ROS2 package for publishing images from Raspberry Pi Camera Module 3',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_publisher = rpi_camera_publisher.camera_publisher:main',
            'camera_subscriber = rpi_camera_publisher.camera_subscriber:main',
        ],
    },
)