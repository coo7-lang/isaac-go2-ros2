import os
import sys
import hydra
import time
import math
import argparse


def _prepend_env_path(name, path):
    if not path or not os.path.exists(path):
        return
    paths = [p for p in os.environ.get(name, "").split(os.pathsep) if p]
    if path in paths:
        paths.remove(path)
    paths.insert(0, path)
    os.environ[name] = os.pathsep.join(paths)


def _prefer_isaacsim_ros2():
    isaacsim_root = os.environ.get("ISAACSIM_PATH")
    if not isaacsim_root:
        default_root = os.path.expanduser("~/isaacsim")
        if os.path.exists(default_root):
            isaacsim_root = default_root
    if not isaacsim_root:
        return

    ros2_root = os.path.join(isaacsim_root, "exts", "isaacsim.ros2.bridge", "humble")
    rclpy_path = os.path.join(ros2_root, "rclpy")
    lib_path = os.path.join(ros2_root, "lib")
    if not os.path.exists(os.path.join(rclpy_path, "rclpy")):
        return

    if rclpy_path in sys.path:
        sys.path.remove(rclpy_path)
    sys.path.insert(0, rclpy_path)
    _prepend_env_path("PYTHONPATH", rclpy_path)
    _prepend_env_path("LD_LIBRARY_PATH", lib_path)
    _prepend_env_path("AMENT_PREFIX_PATH", ros2_root)


_prefer_isaacsim_ros2()
import rclpy


def _env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _prefer_conda_torch():
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix:
        return
    import site
    import sys

    for path in site.getsitepackages([conda_prefix]):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)


_prefer_conda_torch()
import torch
from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Tutorial on running the cartpole RL environment.")

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args

if hasattr(args_cli, "headless"):
    args_cli.headless = _env_flag("HEADLESS", args_cli.headless)
if hasattr(args_cli, "enable_cameras") and os.environ.get("ENABLE_CAMERAS") is not None:
    args_cli.enable_cameras = _env_flag("ENABLE_CAMERAS", args_cli.enable_cameras)

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

from go2.go2_env import Go2RSLEnvCfg, camera_follow
import env.sim_env as sim_env
import go2.go2_sensors as go2_sensors
import omni
import carb
import go2.go2_ctrl as go2_ctrl
import ros2.go2_ros2_bridge as go2_ros2_bridge

FILE_PATH = os.path.join(os.path.dirname(__file__), "cfg")
@hydra.main(config_path=FILE_PATH, config_name="sim", version_base=None)
def run_simulator(cfg):
    is_headless = getattr(args_cli, "headless", False)
    enable_lidar = bool(cfg.sensor.enable_lidar)
    enable_camera = bool(cfg.sensor.enable_camera)
    enable_semantic = enable_camera and bool(cfg.sensor.semantic_segmentation)

    # Go2 Environment setup
    go2_env_cfg = Go2RSLEnvCfg()
    if hasattr(args_cli, "device"):
        go2_env_cfg.sim.device = args_cli.device
    go2_env_cfg.scene.num_envs = cfg.num_envs
    go2_env_cfg.decimation = math.ceil(1./go2_env_cfg.sim.dt/cfg.freq)
    go2_env_cfg.sim.render_interval = go2_env_cfg.decimation
    go2_ctrl.init_base_vel_cmd(cfg.num_envs)
    if cfg.env_name.startswith("obstacle"):
        env, policy = go2_ctrl.get_rsl_rough_policy(go2_env_cfg)
    else:
        env, policy = go2_ctrl.get_rsl_flat_policy(go2_env_cfg)

    # Simulation environment
    if (cfg.env_name == "obstacle-dense"):
        sim_env.create_obstacle_dense_env(enable_semantic=enable_semantic) # obstacles dense
    elif (cfg.env_name == "obstacle-medium"):
        sim_env.create_obstacle_medium_env(enable_semantic=enable_semantic) # obstacles medium
    elif (cfg.env_name == "obstacle-sparse"):
        sim_env.create_obstacle_sparse_env(enable_semantic=enable_semantic) # obstacles sparse
    elif (cfg.env_name == "warehouse"):
        sim_env.create_warehouse_env(enable_semantic=enable_semantic) # warehouse
    elif (cfg.env_name == "warehouse-forklifts"):
        sim_env.create_warehouse_forklifts_env(enable_semantic=enable_semantic) # warehouse forklifts
    elif (cfg.env_name == "warehouse-shelves"):
        sim_env.create_warehouse_shelves_env(enable_semantic=enable_semantic) # warehouse shelves
    elif (cfg.env_name == "full-warehouse"):
        sim_env.create_full_warehouse_env(enable_semantic=enable_semantic) # full warehouse

    # Sensor setup
    sm = go2_sensors.SensorManager(cfg.num_envs)
    lidar_annotators = sm.add_rtx_lidar() if enable_lidar else []
    cameras = sm.add_camera(cfg.freq) if enable_camera else []
    if is_headless and (cfg.sensor.enable_camera or cfg.sensor.enable_lidar):
        print("[isaac_go2_ros2] Headless sensor mode enabled. If Replicator/RTX fails, rerun with sensor flags disabled.")

    # Keyboard control
    if not is_headless:
        system_input = carb.input.acquire_input_interface()
        system_input.subscribe_to_keyboard_events(
            omni.appwindow.get_default_app_window().get_keyboard(), go2_ctrl.sub_keyboard_event)
    
    # ROS2 Bridge
    rclpy.init()
    dm = go2_ros2_bridge.RobotDataManager(env, lidar_annotators, cameras, cfg)
    print("[isaac_go2_ros2] ROS2 bridge initialized.", flush=True)

    # Run simulation
    sim_step_dt = float(go2_env_cfg.sim.dt * go2_env_cfg.decimation)
    obs, _ = env.reset()
    print("[isaac_go2_ros2] Environment reset complete; entering simulation loop.", flush=True)
    while simulation_app.is_running():
        start_time = time.time()
        with torch.inference_mode():
            # control joints
            actions = policy(obs)

            # step the environment
            obs, _, _, _ = env.step(actions)

            # # ROS2 data
            dm.pub_ros2_data()
            rclpy.spin_once(dm, timeout_sec=0.0)

            # Camera follow
            if (cfg.camera_follow and not is_headless):
                camera_follow(env)

            # limit loop time
            elapsed_time = time.time() - start_time
            if elapsed_time < sim_step_dt:
                sleep_duration = sim_step_dt - elapsed_time
                time.sleep(sleep_duration)
        actual_loop_time = time.time() - start_time
        rtf = min(1.0, sim_step_dt/elapsed_time)
        print(f"\rStep time: {actual_loop_time*1000:.2f}ms, Real Time Factor: {rtf:.2f}", end='', flush=True)
    
    dm.destroy_node()
    rclpy.shutdown()
    simulation_app.close()

if __name__ == "__main__":
    run_simulator()
    
