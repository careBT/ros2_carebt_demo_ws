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

from carebt.actionNode import ActionNode
from carebt.nodeStatus import NodeStatus
from nav2_msgs.srv import ManageLifecycleNodes
from std_srvs.srv import Trigger

########################################################################


class Nav2PanelStubs(ActionNode):
    """Minimal lifecycle manager services for the Nav2 rviz panel.

    The panel waits for `<manager>/is_active` before it enables its buttons and
    sends the Startup/Pause/Resume/Reset buttons to `<manager>/manage_nodes`.
    The lifecycle nodes are brought up by the carebt_navigator itself, therefore
    `is_active` always answers `True` and `manage_nodes` commands are ignored.

    The node stays `SUSPENDED` (not ticked) as long as its parent runs. The services
    exist from `on_init` until the node is deleted.
    """

    MANAGERS = ('lifecycle_manager_navigation', 'lifecycle_manager_localization')

    def __init__(self, bt_runner):
        super().__init__(bt_runner)
        self._ros_node = bt_runner.node
        self._services = []

    def on_init(self) -> None:
        for manager in self.MANAGERS:
            self._services.append(self._ros_node.create_service(
                Trigger, f'{manager}/is_active', self._is_active))
            self._services.append(self._ros_node.create_service(
                ManageLifecycleNodes, f'{manager}/manage_nodes', self._manage_nodes))
        self.set_status(NodeStatus.SUSPENDED)

    def on_delete(self) -> None:
        for service in self._services:
            self._ros_node.destroy_service(service)
        self._services = []

    def _is_active(self, request, response):
        response.success = True
        return response

    def _manage_nodes(self, request, response):
        self.get_logger().info('{} - manage_nodes command {} ignored'
                               .format(self.__class__.__name__, request.command))
        response.success = True
        return response
