import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share    = get_package_share_directory('seat_finder')
    sensor_share = get_package_share_directory('sensor')
    nav2_share   = get_package_share_directory('nav2')
    ros_gz_share = get_package_share_directory('ros_gz_sim')
    bt_share     = get_package_share_directory('nav2_bt_navigator')

    world_path   = os.path.join(pkg_share, 'worlds', 'cafe.sdf')
    rviz_config  = os.path.join(pkg_share, 'config', 'cafe.rviz')
    bridge_yaml  = os.path.join(pkg_share, 'config', 'bridge.yaml')
    urdf_path    = os.path.join(sensor_share, 'urdf', 'sensor_robot.urdf')
    map_yaml     = os.path.join(pkg_share, 'maps', 'cafe_map.yaml')
    nav2_params  = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    bt_xml       = os.path.join(bt_share, 'behavior_trees',
                                'navigate_to_pose_w_replanning_and_recovery.xml')

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
        # Bridge
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
                '-y', '-6.0',
                '-z', '0.11',
                '-Y', '0.0',
            ],
            output='screen',
        ),
        # Map server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            parameters=[nav2_params, {'yaml_filename': map_yaml, 'use_sim_time': True}],
            output='screen',
        ),
        # AMCL
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            parameters=[nav2_params, {'use_sim_time': True,
                                      'initial_pose.x': 0.0,
                                      'initial_pose.y': 0.0,
                                      'initial_pose.yaw': 0.0}],
            output='screen',
        ),
        # Lifecycle manager - localization
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            parameters=[{'use_sim_time': True, 'autostart': True,
                         'node_names': ['map_server', 'amcl']}],
            output='screen',
        ),
        # Planner server
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            parameters=[nav2_params, {'use_sim_time': True}],
            output='screen',
        ),
        # Controller server
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            parameters=[nav2_params, {'use_sim_time': True}],
            output='screen',
        ),
        # Behavior server
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            parameters=[nav2_params, {'use_sim_time': True}],
            output='screen',
        ),
        # BT navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            parameters=[nav2_params, {'use_sim_time': True,
                                      'default_nav_to_pose_bt_xml': bt_xml}],
            output='screen',
        ),
        # Lifecycle manager - navigation
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            parameters=[{'use_sim_time': True, 'autostart': True,
                         'node_names': ['planner_server', 'controller_server',
                                        'behavior_server', 'bt_navigator']}],
            output='screen',
        ),
        # Chair detector
        Node(
            package='seat_finder',
            executable='chair_detector',
            name='chair_detector',
            output='screen',
        ),
        # Coord transform
        Node(
            package='seat_finder',
            executable='coord_transform',
            name='coord_transform',
            output='screen',
        ),
        # Seat navigator
        Node(
            package='seat_finder',
            executable='seat_navigator',
            name='seat_navigator',
            output='screen',
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