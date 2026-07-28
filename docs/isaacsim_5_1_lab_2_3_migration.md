# Isaac Sim 5.1 / Isaac Lab 2.3 Migration Notes

## Target

This fork adapts the upstream Isaac Sim 4.5 / Isaac Lab 2.1 branch to:

- Ubuntu 22.04
- ROS2 Humble
- Isaac Sim 5.1.0
- Isaac Lab 2.3.0
- RTX 50-series / Blackwell laptop GPU

The goal is feature equivalence with the upstream 4.5 branch, not only a motion-only demo.

## What Problem This Branch Solves

On RTX 50-series machines, Isaac Sim 4.5 may fail during GUI, RTX rendering, or Replicator initialization. The first compatibility patch made startup more robust by avoiding top-level imports of Replicator, synthetic-data, camera, and RTX lidar modules when those features are disabled.

The branch now targets the next step: run the upstream feature set on Isaac Sim 5.1 / Isaac Lab 2.3 while keeping a motion-only config as a fallback for debugging.

## Default Full-Feature Config

The default `cfg/sim.yaml` is configured for full-feature validation:

- `camera_follow: True`
- `env_name: obstacle-dense`
- `sensor.enable_lidar: True`
- `sensor.enable_camera: True`
- `sensor.color_image: True`
- `sensor.depth_image: True`
- `sensor.semantic_segmentation: True`

Expected ROS2 topics include:

- `/unitree_go2/cmd_vel`
- `/unitree_go2/odom`
- `/unitree_go2/pose`
- `/unitree_go2/front_cam/color_image`
- `/unitree_go2/front_cam/depth_image`
- `/unitree_go2/front_cam/semantic_segmentation_image`
- `/unitree_go2/front_cam/info`
- `/unitree_go2/lidar/point_cloud`

## Motion-Only Fallback Config

`cfg/sim_motion_only.yaml` is a fallback config for startup debugging:

- `camera_follow: False`
- `env_name: warehouse`
- all camera/lidar/semantic flags disabled

Use this only when the full sensor stack fails and you need to confirm that the base Go2 + ROS2 control loop still works.

## Ubuntu Run Commands

Full GUI/sensor validation:

```bash
conda activate isaaclab
source /opt/ros/humble/setup.bash
cd ~/isaacsim
source setup_conda_env.sh
cd /path/to/isaac-go2-ros2
python isaac_go2_ros2.py
```

Headless sensor validation:

```bash
conda activate isaaclab
source /opt/ros/humble/setup.bash
cd ~/isaacsim
source setup_conda_env.sh
cd /path/to/isaac-go2-ros2
HEADLESS=1 ENABLE_CAMERAS=1 python isaac_go2_ros2.py --headless
```

Motion-only fallback:

```bash
conda activate isaaclab
source /opt/ros/humble/setup.bash
cd ~/isaacsim
source setup_conda_env.sh
cd /path/to/isaac-go2-ros2
HEADLESS=1 ENABLE_CAMERAS=0 python isaac_go2_ros2.py --headless --config-name sim_motion_only
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

## Validation Order

If the full config fails, validate one layer at a time:

1. Motion-only fallback: `/cmd_vel`, `/odom`, `/pose`.
2. RGB camera: `/unitree_go2/front_cam/color_image`, `/unitree_go2/front_cam/info`.
3. Depth image: `/unitree_go2/front_cam/depth_image`.
4. Semantic segmentation: `/unitree_go2/front_cam/semantic_segmentation_image`.
5. RTX lidar: `/unitree_go2/lidar/point_cloud`.
6. RViz visualization with `rviz/go2.rviz`.

## Changed Files

- `isaac_go2_ros2.py`
  - Uses `parse_known_args()` so Hydra config overrides such as `--config-name sim_motion_only` work together with Isaac Lab app launcher args.
  - Adds environment-variable handling for `HEADLESS` and `ENABLE_CAMERAS`.
  - Prefers conda `torch/torchvision` paths before importing Isaac Sim modules.
  - Skips keyboard control and camera-follow logic in headless mode.
  - Creates camera/lidar objects only when enabled by config.

- `cfg/sim.yaml`
  - Restores the upstream-style full sensor defaults for Isaac Sim 5.1 validation.

- `cfg/sim_motion_only.yaml`
  - Keeps a conservative sensor-disabled fallback config.

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

## Known Limits

This patch prepares the branch for full-feature validation on Isaac Sim 5.1 / Isaac Lab 2.3, but camera, semantic segmentation, and RTX lidar still need to be verified on the Ubuntu machine with Isaac Sim 5.1 installed.
