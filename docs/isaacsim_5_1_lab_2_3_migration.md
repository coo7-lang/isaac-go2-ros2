# Isaac Sim 5.1 / Isaac Lab 2.3 Migration Notes

## Target

This fork is being adapted from the upstream Isaac Sim 4.5 / Isaac Lab 2.1 branch to:

- Ubuntu 22.04
- ROS2 Humble
- Isaac Sim 5.1.0
- Isaac Lab 2.3.0
- RTX 50-series / Blackwell laptop GPU

## Why This Patch Exists

On RTX 50-series machines, Isaac Sim 4.5 may fail during GUI or RTX rendering initialization. The first goal of this branch is therefore to run a headless, motion-only Go2 smoke test before enabling camera, semantic segmentation, and RTX lidar.

The original code imported Replicator and synthetic-data modules at file import time. That means the program could fail before the robot simulation starts, even when camera/lidar are disabled in `cfg/sim.yaml`. This patch moves those imports into the functions that actually need them.

## Smoke Test Scope

The default `cfg/sim.yaml` is configured for:

- `camera_follow: False`
- `sensor.enable_lidar: False`
- `sensor.enable_camera: False`
- `sensor.color_image: False`
- `sensor.depth_image: False`
- `sensor.semantic_segmentation: False`

This should still publish the basic robot-control ROS2 topics:

- `/unitree_go2/cmd_vel`
- `/unitree_go2/odom`
- `/unitree_go2/pose`

Camera and lidar topics are intentionally disabled until the base simulation is confirmed.

## Ubuntu Run Commands

```bash
conda activate isaaclab
source /opt/ros/humble/setup.bash
cd ~/isaacsim
source setup_conda_env.sh
cd /path/to/isaac-go2-ros2
HEADLESS=1 ENABLE_CAMERAS=0 python isaac_go2_ros2.py --headless
```

In another terminal:

```bash
source /opt/ros/humble/setup.bash
ros2 topic list
ros2 topic echo /unitree_go2/odom
```

To send a simple velocity command:

```bash
source /opt/ros/humble/setup.bash
ros2 topic pub /unitree_go2/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" --once
```

## Sensor Re-enable Plan

After the motion-only smoke test works:

1. Enable `sensor.enable_camera: True` and `sensor.color_image: True`.
2. Verify `/unitree_go2/front_cam/color_image`.
3. Enable `sensor.depth_image: True`.
4. Verify `/unitree_go2/front_cam/depth_image`.
5. Enable `sensor.semantic_segmentation: True`.
6. Verify semantic labels and visualization.
7. Enable `sensor.enable_lidar: True`.
8. Verify `/unitree_go2/lidar/point_cloud`.

If Replicator or RTX lidar still fails, keep the motion-only branch working and debug sensors separately.

## Changed Files

- `isaac_go2_ros2.py`
  - Adds environment-variable handling for `HEADLESS` and `ENABLE_CAMERAS`.
  - Prefers conda `torch/torchvision` paths before importing Isaac Sim modules.
  - Skips keyboard control and camera-follow logic in headless mode.
  - Creates camera/lidar objects only when enabled by config.

- `env/sim_env.py`
  - Makes `omni.replicator.core` a lazy optional import.
  - Skips semantic labels if Replicator is unavailable.

- `go2/go2_sensors.py`
  - Imports camera and RTX lidar dependencies only inside the sensor functions.
  - Raises a clear error if RTX lidar is enabled but Replicator is unavailable.

- `ros2/go2_ros2_bridge.py`
  - Enables either the new `isaacsim.ros2.bridge` extension name or the older `omni.isaac.ros2_bridge` name.
  - Imports Replicator/synthetic-data modules only when camera publishers are created.
  - Imports `cv_bridge`/`cv2` only when semantic segmentation images are processed.

- `cfg/sim.yaml`
  - Sets a conservative headless, sensor-disabled smoke-test default.

## Known Limits

This patch is not a full validation of all Isaac Sim 5.1 / Isaac Lab 2.3 API changes. It is a minimal migration patch to unblock the first experiment step: basic Go2 simulation plus ROS2 motion-control topics.

Full camera, semantic segmentation, and RTX lidar behavior still need to be tested on the Ubuntu machine with Isaac Sim 5.1 installed.
