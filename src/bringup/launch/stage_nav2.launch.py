import os
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage_world_utils import (  # noqa: E402
    find_map_yaml, find_robot_pose, read_world, resolve_world, write_amcl_initial_pose)


def launch_setup(context):
    bringup_dir = get_package_share_directory('bringup')
    nav2_dir = get_package_share_directory('nav2_bringup')

    world_file = resolve_world(context.launch_configurations['world'], bringup_dir)

    text = read_world(world_file)
    map_yaml = find_map_yaml(world_file, text)
    params_file = context.launch_configurations['params_file']
    actions = [LogInfo(msg=f'world: {world_file}, map: {map_yaml}')]

    pose = find_robot_pose(text)
    if pose:
        params_file = write_amcl_initial_pose(
            params_file, os.path.splitext(os.path.basename(world_file))[0], pose)
        actions.append(LogInfo(msg=f'initial pose from world file: {pose}'))
    else:
        actions.append(LogInfo(msg='No robot pose found in world file, using params file pose'))

    actions += [
        # Nav2 on kilted publishes TwistStamped on cmd_vel
        Node(
            package='stage_ros2',
            executable='stage_ros2',
            name='stage',
            parameters=[{'world_file': world_file, 'use_stamped_velocity': True}]),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_dir, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': map_yaml,
                'params_file': params_file,
                'use_sim_time': 'true',
                'use_keepout_zones': 'False',
                'use_speed_zones': 'False',
                'autostart': 'true',
            }.items()),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution(
                [nav2_dir, 'rviz', 'nav2_default_view.rviz'])],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
            output='screen'),
    ]
    return actions


def generate_launch_description():
    bringup_dir = get_package_share_directory('bringup')

    return LaunchDescription([
        DeclareLaunchArgument(
            'world', default_value='cave',
            description='World name in bringup/worlds (.world optional) or absolute path. '
                        'The map is maps/<bitmap name>.yaml next to the world file'),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(bringup_dir, 'config', 'stage_nav2_params.yaml'),
            description='Nav2 parameter file'),
        DeclareLaunchArgument(
            'rviz', default_value='True', description='Whether to start rviz2'),
        OpaqueFunction(function=launch_setup),
    ])
