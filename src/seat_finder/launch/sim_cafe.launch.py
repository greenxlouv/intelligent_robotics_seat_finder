import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share     = get_package_share_directory('seat_finder')
    sensor_share  = get_package_share_directory('sensor')
    slam_share    = get_package_share_directory('slam_toolbox')
    ros_gz_share  = get_package_share_directory('ros_gz_sim')

    world_path   = os.path.join(pkg_share, 'worlds', 'cafe.sdf')
    rviz_config  = os.path.join(pkg_share, 'config', 'cafe.rviz')
    bridge_yaml  = os.path.join(pkg_share, 'config', 'bridge.yaml')
    urdf_path    = os.path.join(sensor_share, 'urdf', 'sensor_robot.urdf')

    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        # Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ros_gz_share, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments=[('gz_args', ['-r ', world_path])],
        ),
        # Bridge (cafe world용)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': bridge_yaml}],
            output='screen',
        ),
        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
            output='screen',
        ),
        # Spawn robot
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-topic', 'robot_description',
                '-name', 'sensor_robot',
                '-x', '0.0',
                '-y', '-6.5',
                '-z', '0.11',
                '-Y', '1.5708',
            ],
            output='screen',
        ),
        # SLAM
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_share, 'launch', 'online_async_launch.py')
            ),
            launch_arguments={
                'slam_params_file': os.path.join(get_package_share_directory('slam'), 'config', 'slam_params.yaml'),
                'use_sim_time': 'true',
            }.items(),
        ),
        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': True}],
            output='screen',
        ),
    ])