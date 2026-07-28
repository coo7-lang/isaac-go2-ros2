#  Isaac Sim Unitree Go2 ROS2
[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://docs.python.org/3/whatsnew/3.10.html)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-orange.svg)](https://docs.ros.org/en/humble/index.html)
[![IsaacSim](https://img.shields.io/badge/IsaacSim-5.1.0-red.svg)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html)
[![IsaacLab](https://img.shields.io/badge/IsaacLab-2.3.0-purple.svg)](https://isaac-sim.github.io/IsaacLab/)
[![Linux platform](https://img.shields.io/badge/platform-Ubuntu--22.04-green.svg)](https://releases.ubuntu.com/22.04/)

This fork targets Isaac Sim 5.1.0 and Isaac Lab 2.3.0 for RTX 50-series / Blackwell machines.
The original upstream branch targets Isaac Sim 4.5 and Isaac Lab 2.1.

The default configuration now aims to restore the upstream full feature set on Isaac Sim 5.1: Go2 motion control, ROS2 bridge, RGB camera, depth image, semantic segmentation, and RTX lidar. A separate `cfg/sim_motion_only.yaml` is kept as a fallback smoke-test config when debugging startup or sensor issues.

## Branch Notes: Isaac Sim 5.1 / Isaac Lab 2.3

This branch is a compatibility branch for testing the project on a newer Isaac stack:

- Target runtime: Isaac Sim 5.1.0, Isaac Lab 2.3.0, ROS2 Humble, Ubuntu 22.04.
- Main reason: RTX 50-series / Blackwell GPUs may have rendering or RTX sensor issues with the original Isaac Sim 4.5 setup.
- First validation goal: confirm Go2 simulation, ROS2 bridge, `/cmd_vel`, `/odom`, and `/pose`.
- Full-feature validation goal: confirm RGB camera, depth, semantic segmentation, RTX lidar, and RViz topics on Isaac Sim 5.1.
- Fallback validation goal: use `cfg/sim_motion_only.yaml` if the full sensor stack fails, then re-enable sensors one by one.

Compared with the upstream Isaac Sim 4.5 branch, this branch changes:

- `README.md`: documents the Isaac Sim 5.1 / Isaac Lab 2.3 target and Ubuntu run commands.
- `cfg/sim.yaml`: restores the upstream-style full sensor default for Isaac Sim 5.1 validation.
- `cfg/sim_motion_only.yaml`: keeps a conservative sensor-disabled fallback config for startup debugging.
- `isaac_go2_ros2.py`: supports `HEADLESS` / `ENABLE_CAMERAS` environment flags, prefers conda PyTorch packages, and skips GUI-only logic in headless mode.
- `env/sim_env.py`: makes `omni.replicator.core` optional for environment creation, so semantic labels do not block motion-only runs.
- `go2/go2_sensors.py`: loads camera and RTX lidar dependencies only when those sensors are enabled.
- `ros2/go2_ros2_bridge.py`: supports both newer and older ROS2 bridge extension names and delays camera/semantic dependencies until needed.

More details are in `docs/isaacsim_5_1_lab_2_3_migration.md`.

Please check ```isaacsim-4.2``` branch for isaac sim 4.2 version.

Please check ```isaacsim-4.5-docker``` branch if you want to run inside a docker.

Welcome to the Isaac Sim Unitree Go2 repository! This repository provides a Unitree Go2 quadruped robot simulation, leveraging the Isaac Sim/Isaac Lab framework and integrating seamlessly with a ROS 2 interface. It offers a flexible platform for testing navigation, decision-making, and other autonomous tasks in various scenarios.


<table>
  <tr>
    <td><img src="media/sim-demo1.gif" style="width: 100%;"></td>
    <td><img src="media/sim-demo2.gif" style="width: 100%;"></td>
  </tr>
</table>


## Installation Guide
**Step 0:** Install [Isaac Sim 5.1.0](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html) (Download and extract contents in `${HOME}/isaacsim`)

**Step I:** Please follow the [Isaac Lab official documentation](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/binaries_installation.html) to install Isaac Lab 2.3.0.

**Step II:** Please install [ROS2 Humble](https://docs.ros.org/en/humble/index.html) with the official installation guide.

**Step III:** Install the prerequisite C extension in the conda environment. [reference link](https://stackoverflow.com/questions/58424974/anaconda-importerror-usr-lib64-libstdc-so-6-version-glibcxx-3-4-21-not-fo)
```bash
# default conda env for Isaac Lab
conda activate isaaclab
```

**Step IV:** Clone this repo to your local directory.
```bash
git clone https://github.com/coo7-lang/isaac-go2-ros2.git
```

## Run Unitree Go2 Simulation 
Before running, make sure the branch is checked out:

```bash
git clone https://github.com/coo7-lang/isaac-go2-ros2.git
cd isaac-go2-ros2
git checkout isaacsim-5.1-lab-2.3
```

For full-feature validation, start with the default config:

```bash
conda activate isaaclab
source /opt/ros/humble/setup.bash
cd ~/isaacsim
source setup_conda_env.sh
cd /path/to/isaac-go2-ros2
python isaac_go2_ros2.py
```

If GUI is unstable but the sensor stack should still be tested, run headless with cameras enabled:

```bash
conda activate isaaclab
source /opt/ros/humble/setup.bash
cd ~/isaacsim
source setup_conda_env.sh
cd /path/to/isaac-go2-ros2
HEADLESS=1 ENABLE_CAMERAS=1 python isaac_go2_ros2.py --headless
```

If startup or RTX sensor initialization fails, run the motion-only fallback:

```bash
conda activate isaaclab
source /opt/ros/humble/setup.bash
cd ~/isaacsim
source setup_conda_env.sh
cd /path/to/isaac-go2-ros2
HEADLESS=1 ENABLE_CAMERAS=0 python isaac_go2_ros2.py --headless --config-name sim_motion_only
```

In another terminal, check whether ROS2 topics are published:

```bash
source /opt/ros/humble/setup.bash
ros2 topic list
ros2 topic echo /unitree_go2/odom
```

Send a simple velocity command:

```bash
source /opt/ros/humble/setup.bash
ros2 topic pub /unitree_go2/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" --once
```

Once the simulation is loaded, the robot can be teleoperated by the keyboard:

```W```: Forward, ```A```: Left, ```S```: Backward, ```D```: Right, ```Z```: Left Turn, ```C```: Right Turn.

## Code Reading Guide

Suggested reading order for this branch:

- `isaac_go2_ros2.py`: main entry point. It launches Isaac Sim, creates the Go2 environment, adds optional sensors, starts ROS2, and runs the simulation loop.
- `cfg/sim.yaml`: runtime configuration. This controls environment name, number of robots, frequency, camera/lidar flags, and headless-friendly defaults.
- `go2/go2_env.py`: Isaac Lab environment definition for the Unitree Go2 robot, observations, actions, command interface, and simulation settings.
- `go2/go2_ctrl.py`: low-level RL policy loading and `/cmd_vel` command handling.
- `go2/go2_sensors.py`: optional camera and RTX lidar creation.
- `ros2/go2_ros2_bridge.py`: ROS2 publishers/subscribers for command, odometry, pose, camera, semantic segmentation, and lidar topics.
- `env/sim_env.py`: warehouse and obstacle environment loading.


https://github.com/user-attachments/assets/7abb41fd-26f7-4e5d-bc7f-98ee10467a6a


## ROS2 Topics and Visualization
After launching the simulation, the ROS2 data can be visualized in ```Rviz2```:
```
rviz2 -d /path/to/isaac-go2-ros2/rviz/go2.rviz
```
![rviz](https://github.com/user-attachments/assets/946b6a31-b52a-4153-b337-846087fc2b7d)

Here is a categorized list of ROS 2 topics available for the Unitree Go2:

**Command and Control**  
- `/unitree_go2/cmd_vel`:  Topic to send velocity commands to the robot for motion control.

**Front Camera**  
- `/unitree_go2/front_cam/color_image`: Publishes RGB color images captured by the front camera.
- `/unitree_go2/front_cam/depth_image`: Publishes depth images from the front camera.
- `unitree_go2/front_cam/semantic_segmentation_image`: Publishes semantic segmentation images from the front camera.
- `/unitree_go2/front_cam/info`: Publishes camera information, including intrinsic parameters.

**LIDAR**  
- `/unitree_go2/lidar/point_cloud`:  Publishes a point cloud generated by the robot's LIDAR sensor.

**Odometry and Localization**  
- `/unitree_go2/odom`:  Publishes odometry data, including the robot's position, orientation, and velocity.
- `/unitree_go2/pose`:  Publishes the current pose of the robot in the world frame.


## Simulation Environments & settings
The simulation environments and settings can be changed in ```isaac-go2-ros2/cfg/sim.yaml``` config file. 

#### Launch different simulation environments
The current implementation contains a few environments which can be found on ```isaac-go2-ros2/env/sim_env.py```, which follows standard Isaac Sim method for importing USD environments. To change the environment, please change the ```env_name``` in the config file ```isaac-go2-ros2/cfg/sim.yaml```. Current available environments:
- ```warehouse```: A simple warehouse environment in Isaac Sim.
- ```warehouse-forklifts```: A warehouse environment with forklifts.
- ```warehouse-shelves```: A warehouse environment with shelves.
- ```full-warehouse```: A full warehouse environment containing everything.
- ```obstacle-sparse```: A sparse obstacle field environment.
- ```obstacle-medium```: A  medium obstacle field environment.
- ```obstacle-dense```: A dense obstacle field environment.


#### Launch multiple robots in the environment
This repository supports running multiple Unitree Go2 robots and the number of robots can by changed by the ```num_envs``` parameter in the config file ```isaac-go2-ros2/cfg/sim.yaml```. The following shows an example video.

https://github.com/user-attachments/assets/47ef05c1-5124-4feb-afc8-a3f2c306a212




## Example Usage
The video shows an example of using this repo with an [RL agent](https://github.com/Zhefan-Xu/NavRL) to achieve navigation and collision avoidance:


https://github.com/user-attachments/assets/ccc986c6-bf94-41fe-a4d5-3417ce8b3384

## Acknowledgement
The Go2 controller is based on the RL controller implemented in [go2_omniverse](https://github.com/abizovnuralem/go2_omniverse).





