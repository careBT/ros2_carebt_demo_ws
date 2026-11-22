# careBT demo workspace

This repository demonstrates [careBT](https://github.com/careBT/carebt_core) and its ROS 2 
binding [carebt_ros2](https://github.com/careBT/carebt_ros2). The demos run a simulated robot
in [Stage](https://github.com/careBT/Stage) with Nav2 on ROS 2 Kilted.

## Getting started

The workspace is set up as a VS Code dev container based on `althack/ros2:kilted-full`.

1. Clone the repository including its submodules:

   ```bash
   git clone --recurse-submodules git@github.com:careBT/ros2_carebt_demo_ws.git
   ```

   In an existing clone run `git submodule update --init --recursive`.

2. Open the folder in VS Code and choose `Reopen in Container`.
   The `postCreateCommand` runs `rosdep` and installs `carebt_core` in editable mode.
   Nav2 and `rclpy_message_converter` are installed from apt.

3. Build the workspace with the VS Code task `build` or:

   ```bash
   colcon build --merge-install --symlink-install
   source install/setup.bash
   ```

## Packages

| Path | Content |
| --- | --- |
| `src/carebt_core` | careBT Python library (pip installed editable, not a colcon package) |
| `src/carebt_ros2` | careBT ROS 2 binding, branch `kilted` |
| `src/carebt_navigator` | careBT navigator |
| `src/Stage` | Stage simulator, branch `ros2` |
| `src/stage_ros2` | ROS 2 bridge for Stage, branch `jazzy` |
| `src/bringup` | launch files, Nav2 parameters, worlds and maps for Stage |

## Demos

### 1. Stage Nav2 Navigator Demo

A robot in the Stage `cave` world navigated by the standard Nav2 stack. `nav2_bringup` starts
the Nav2 servers, the lifecycle manager and the Nav2 `bt_navigator`. Map and initial pose are
taken from the world file. Send goals in rviz2 with the `Nav2 Goal` tool or the waypoint mode
of the Nav2 panel.

```bash
ros2 launch bringup stage_nav2.launch.py
```

Launch arguments:

* `world:=<name or absolute path>` world from `src/bringup/worlds` (default `cave`)
* `rviz:=False` to start without rviz2
* `params_file:=<path>` Nav2 parameter file (default [src/bringup/config/stage_nav2_params.yaml](src/bringup/config/stage_nav2_params.yaml))

### 2. Stage Nav2 careBT Navigator Demo

A robot in the Stage `cave` world navigated by the Nav2 servers (map server, AMCL, planner,
smoother, controller, velocity smoother, collision monitor), orchestrated by the
`carebt_navigator`.
The careBT navigator

* configures and activates the Nav2 lifecycle nodes,
* publishes the initial pose from the world file until the robot is localized,
* serves the Nav2 actions `navigate_to_pose`, `navigate_through_poses` and `follow_waypoints`,
* provides the lifecycle manager services used by the Nav2 rviz panel.

Send goals in rviz2 with the `Nav2 Goal` tool or the waypoint mode of the Nav2 panel.

```bash
ros2 launch bringup demo_carebt_navigator.launch.py
```

Launch arguments:

* `world:=<name or absolute path>` world from `src/bringup/worlds` (default `cave`)
* `rviz:=False` to start without rviz2
* `params_file:=<path>` parameter file for the Nav2 servers and the careBT navigator (default [src/bringup/config/carebt_navigator_params.yaml](src/bringup/config/carebt_navigator_params.yaml))
