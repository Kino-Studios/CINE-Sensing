from setuptools import find_packages, setup

package_name = 'depth_publisher'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/depth_publisher_launch.py']),
        ('share/' + package_name + '/config', ['config/depth_publisher_params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fishnos',
    maintainer_email='fishnos@todo.todo',
    description='ROS2 package for publishing depth maps using Depth-Anything AI model',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'depth_publisher_node = depth_publisher.depth_publisher_node:main',
            'depth_visualizer_node = depth_publisher.depth_visualizer_node:main',
        ],
    },
)