import os
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage_world_utils import (  # noqa: E402
    find_map_yaml, find_robot_pose, read_world, resolve_world)


def launch_setup(context):
    bringup_dir = get_package_share_directory('bringup')
    nav2_dir = get_package_share_directory('nav2_bringup')

    world_file = resolve_world(context.launch_configurations['world'], bringup_dir)
    text = read_world(world_file)
    map_yaml = find_map_yaml(world_file, text)
    params_file = context.launch_configurations['params_file']
    actions = [LogInfo(msg=f'world: {world_file}, map: {map_yaml}')]

    carebt_params = [params_file, {'use_sim_time': True}]
    pose = find_robot_pose(text)
    if pose:
        carebt_params[1]['initial_pose'] = list(pose)
        actions.append(LogInfo(msg=f'initial pose from world file: {pose}'))
    else:
        actions.append(LogInfo(msg='No robot pose found in world file, using initial_pose param'))

    # no lifecycle manager: the carebt_navigator configures and activates the lifecycle nodes
    nav2_params = [params_file, {'use_sim_time': True}]

    def nav2_node(package, executable, remappings=None, extra_params=None):
        return Node(
            package=package,
            executable=executable,
            name=executable,
            output='screen',
            parameters=nav2_params + ([extra_params] if extra_params else []),
            remappings=remappings or [])

    actions += [
        # Nav2 on kilted publishes TwistStamped on cmd_vel
        Node(
            package='stage_ros2',
            executable='stage_ros2',
            name='stage',
            parameters=[{'world_file': world_file, 'use_stamped_velocity': True}]),

        nav2_node('nav2_map_server', 'map_server', extra_params={'yaml_filename': map_yaml}),
        nav2_node('nav2_amcl', 'amcl'),
        nav2_node('nav2_planner', 'planner_server'),
        nav2_node('nav2_smoother', 'smoother_server'),
        nav2_node('nav2_controller', 'controller_server',
                  remappings=[('cmd_vel', 'cmd_vel_nav')]),
        nav2_node('nav2_velocity_smoother', 'velocity_smoother',
                  remappings=[('cmd_vel', 'cmd_vel_nav')]),
        nav2_node('nav2_collision_monitor', 'collision_monitor'),

        Node(
            package='carebt_navigator',
            executable='carebt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=carebt_params),

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
            default_value=os.path.join(bringup_dir, 'config', 'carebt_navigator_params.yaml'),
            description='Parameter file for the Nav2 servers and the carebt_navigator'),
        DeclareLaunchArgument(
            'rviz', default_value='True', description='Whether to start rviz2'),
        OpaqueFunction(function=launch_setup),
    ])
