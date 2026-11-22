# Copyright 2025 Andreas Steck (steck.andi@gmail.com)
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

import math

from carebt.actionNode import ActionNode
from carebt.nodeStatus import NodeStatus
from carebt.sequenceNode import SequenceNode
from carebt_nav2.utility_nodes import LifecycleClient
from geometry_msgs.msg import PoseWithCovarianceStamped
import rclpy
from tf2_ros import TransformException

# lifecycle transition ids
CONFIGURE = 1
ACTIVATE = 3

########################################################################


class GetInitialPoseFromParams(ActionNode):
    """Creates the initial pose from the ROS parameters.

    The parameter `initial_pose` is a list [x, y, yaw] (m, m, rad) in the `map` frame.
    The parameters `initial_pose_var_xy` and `initial_pose_var_yaw` are the variances.

    Output Parameters
    -----------------
    ?initial_pose : geometry_msgs.msg.PoseWithCovarianceStamped
        The initial pose
    """

    def __init__(self, bt_runner):
        super().__init__(bt_runner, '=> ?initial_pose')
        self.__node = bt_runner.node

    def on_init(self) -> None:
        x, y, yaw = self.__node.get_parameter('initial_pose').value
        pose = PoseWithCovarianceStamped()
        pose.header.frame_id = 'map'
        pose.pose.pose.position.x = float(x)
        pose.pose.pose.position.y = float(y)
        pose.pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.pose.orientation.w = math.cos(yaw / 2.0)
        var_xy = self.__node.get_parameter('initial_pose_var_xy').value
        pose.pose.covariance[0] = var_xy
        pose.pose.covariance[7] = var_xy
        pose.pose.covariance[35] = self.__node.get_parameter('initial_pose_var_yaw').value
        self._initial_pose = pose
        self.set_status(NodeStatus.SUCCESS)

########################################################################


class InitPoseUntilLocalized(ActionNode):
    """Publishes the initial pose until the localization provides the transform.

    The pose is published repeatedly, because a single message gets lost if the
    localization has not yet discovered the publisher. The node succeeds as soon as
    the transform from `map` to `base_link` is within the pose covariance.

    Input Parameters
    ----------------
    ?initial_pose : geometry_msgs.msg.PoseWithCovarianceStamped
        The initial pose
    """

    def __init__(self, bt_runner):
        super().__init__(bt_runner, '?initial_pose')
        self.__node = bt_runner.node
        self.__tf_buffer = bt_runner.tf_buffer
        self.__pub = None
        self.__tick_count = 0
        self.set_throttle_ms(100)
        self.set_timeout(20000)

    def on_init(self) -> None:
        self.__pub = self.__node.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)

    def __localized(self) -> bool:
        try:
            trans = self.__tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
        except TransformException:
            return False
        pose = self._initial_pose.pose
        return (abs(trans.transform.translation.x - pose.pose.position.x)
                < math.sqrt(pose.covariance[0])
                and abs(trans.transform.translation.y - pose.pose.position.y)
                < math.sqrt(pose.covariance[7]))

    def on_tick(self) -> None:
        # publish once per second (every 10th tick), check the transform every tick
        if self.__tick_count % 10 == 0:
            self.__pub.publish(self._initial_pose)
        self.__tick_count += 1
        if self.__localized():
            self.get_logger().info('{} - localization pose ok'.format(self.__class__.__name__))
            self.set_status(NodeStatus.SUCCESS)

    def on_timeout(self) -> None:
        self.set_status(NodeStatus.FAILURE)
        self.set_contingency_message('NOT_LOCALIZED')

    def on_delete(self) -> None:
        if self.__pub is not None:
            self.__node.destroy_publisher(self.__pub)
            self.__pub = None

########################################################################


class StartLifecycleNodes(SequenceNode):
    """Configures and activates the lifecycle nodes of a ROS parameter one after another.

    Input Parameters
    ----------------
    ?param : str
        The name of the ROS parameter containing the list of lifecycle node names
    """

    def __init__(self, bt_runner):
        super().__init__(bt_runner, '?param')

    def on_init(self) -> None:
        for name in self.bt_runner.node.get_parameter(self._param).value:
            self.append_child(LifecycleClient, f"'{name}' {CONFIGURE}")
            self.append_child(LifecycleClient, f"'{name}' {ACTIVATE}")

########################################################################


class NavigatorStartup(SequenceNode):
    """Brings up localization and navigation servers.

    1. configure and activate `localization_nodes`
    2. publish the initial pose and wait until the localization provides the transform
    3. configure and activate `navigation_nodes`
    """

    def __init__(self, bt_runner):
        super().__init__(bt_runner)
        self._initial_pose = None

    def on_init(self) -> None:
        self.append_child(StartLifecycleNodes, "'localization_nodes'")
        self.append_child(GetInitialPoseFromParams, '=> ?initial_pose')
        self.append_child(InitPoseUntilLocalized, '?initial_pose')
        self.append_child(StartLifecycleNodes, "'navigation_nodes'")
