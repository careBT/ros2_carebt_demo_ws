# Copyright 2021 Andreas Steck (steck.andi@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from carebt import LogLevel
from carebt_navigator.bt_navigator_nodes import NavigatorMain
from carebt_ros2 import RosCarebtRunner
from carebt_ros2.plugins.odom_smoother import OdomSmoother
from rclpy.duration import Duration
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

########################################################################


def main():
    rosCarebtRunner = RosCarebtRunner('bt_navigator')
    rosCarebtRunner.get_bt_runner().get_logger().set_log_level(LogLevel.INFO)
    rosCarebtRunner.get_bt_runner().odom_smoother = OdomSmoother(rosCarebtRunner,
                                                                 'odom',
                                                                 Duration(nanoseconds=500000000))
    
    rosCarebtRunner.get_bt_runner().tf_buffer = Buffer()
    rosCarebtRunner.get_bt_runner().tf_listener = TransformListener(
        rosCarebtRunner.get_bt_runner().tf_buffer, rosCarebtRunner)
    rosCarebtRunner.declare_parameter('waypoint_action', 'WaitAction')

    # startup: bring up localization and navigation servers via their lifecycle services
    rosCarebtRunner.declare_parameter('localization_nodes', ['map_server', 'amcl'])
    rosCarebtRunner.declare_parameter('navigation_nodes', ['planner_server',
                                                           'controller_server',
                                                           'velocity_smoother',
                                                           'collision_monitor'])
    rosCarebtRunner.declare_parameter('initial_pose', [0.0, 0.0, 0.0])  # x, y, yaw
    rosCarebtRunner.declare_parameter('initial_pose_var_xy', 0.25)
    rosCarebtRunner.declare_parameter('initial_pose_var_yaw', 0.07)

    rosCarebtRunner.run(NavigatorMain)



if __name__ == '__main__':
    main()
