#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_SH="${CONDA_SH:-/home/lion/miniconda3/etc/profile.d/conda.sh}"
CONDA_ENV="${CONDA_ENV:-lab}"
ISAACSIM_PATH="${ISAACSIM_PATH:-/home/lion/isaacsim}"
DEVICE="${DEVICE:-cpu}"
HEADLESS=0
ENABLE_CAMERAS_VALUE="${ENABLE_CAMERAS:-0}"

usage() {
    cat <<EOF
Usage: $(basename "$0") [--headless|--gui] [--device cpu|cuda:0] [--enable-cameras] [--] [extra isaac_go2_ros2.py args...]

Examples:
  $(basename "$0") --headless --device cpu
  $(basename "$0") --gui --device cpu sensor.enable_lidar=False sensor.enable_camera=False
  DEVICE=cuda:0 $(basename "$0") --gui

This launcher intentionally does not source /opt/ros/humble/setup.bash.
Use system ROS2 CLI/RViz in a separate terminal so Python 3.10 ROS packages do not
contaminate the Isaac Sim / Isaac Lab Python 3.11 process.
EOF
}

EXTRA_ARGS=()
while (($#)); do
    case "$1" in
        --headless)
            HEADLESS=1
            shift
            ;;
        --gui)
            HEADLESS=0
            shift
            ;;
        --device)
            DEVICE="${2:?--device requires a value}"
            shift 2
            ;;
        --enable-cameras)
            ENABLE_CAMERAS_VALUE=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            EXTRA_ARGS+=("$@")
            break
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ ! -f "$CONDA_SH" ]]; then
    echo "Conda activation script not found: $CONDA_SH" >&2
    exit 1
fi
if [[ ! -d "$ISAACSIM_PATH" ]]; then
    echo "Isaac Sim path not found: $ISAACSIM_PATH" >&2
    exit 1
fi
if [[ ! -f "$ISAACSIM_PATH/setup_conda_env.sh" ]]; then
    echo "Isaac Sim setup script not found: $ISAACSIM_PATH/setup_conda_env.sh" >&2
    exit 1
fi

# Load conda and Isaac Sim's Python 3.11 runtime support.
# Conda activation hooks and Isaac Sim's setup scripts read optional shell variables
# that may be unset, so do not keep nounset enabled while sourcing them.
set +u
# shellcheck disable=SC1090
source "$CONDA_SH"
conda activate "$CONDA_ENV"
export ISAACSIM_PATH
# shellcheck disable=SC1090
source "$ISAACSIM_PATH/setup_conda_env.sh"
set -u

# Avoid leaking system ROS2 Humble Python 3.10 packages into Isaac's Python 3.11 process.
# DDS variables are preserved so separate ROS2 terminals can communicate with the app.
unset PYTHONHOME
if [[ -n "${PYTHONPATH:-}" ]]; then
    CLEANED_PYTHONPATH="$(python - <<'PY'
import os
parts = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
parts = [p for p in parts if "/opt/ros/humble" not in p and "python3.10" not in p]
print(os.pathsep.join(parts))
PY
)"
    export PYTHONPATH="$CLEANED_PYTHONPATH"
fi

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
export ENABLE_CAMERAS="$ENABLE_CAMERAS_VALUE"

CMD=(python "$PROJECT_ROOT/isaac_go2_ros2.py" --device "$DEVICE")
if (( HEADLESS )); then
    export HEADLESS=1
    CMD+=(--headless)
else
    export HEADLESS=0
fi
CMD+=("${EXTRA_ARGS[@]}")

cd "$PROJECT_ROOT"
echo "[run_isaac_go2] project: $PROJECT_ROOT"
echo "[run_isaac_go2] conda env: $CONDA_ENV"
echo "[run_isaac_go2] Isaac Sim: $ISAACSIM_PATH"
echo "[run_isaac_go2] device: $DEVICE"
echo "[run_isaac_go2] headless: $HEADLESS"
echo "[run_isaac_go2] ENABLE_CAMERAS: $ENABLE_CAMERAS"
echo "[run_isaac_go2] ROS_DOMAIN_ID: $ROS_DOMAIN_ID"
echo "[run_isaac_go2] RMW_IMPLEMENTATION: $RMW_IMPLEMENTATION"
echo "[run_isaac_go2] command: ${CMD[*]}"
exec "${CMD[@]}"
