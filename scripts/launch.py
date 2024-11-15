# ~ launch.py | by: ANXETY ~

from json_utils import read_json, save_json, update_json    # JSON (main)
from TunnelHub import Tunnel                                # Tunneling

from IPython.display import clear_output
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import pickle
import time
import json
import os
import re


# Constants
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

UI = read_json(SETTINGS_PATH, 'WEBUI.current')
WEBUI = read_json(SETTINGS_PATH, 'WEBUI.webui_path')
ENV_NAME = read_json(SETTINGS_PATH, 'ENVIRONMENT.env_name')

def load_settings(path):
    if not os.path.exists(path):
        return {}
    try:
        _environment = read_json(path, 'ENVIRONMENT')
        _widgets = read_json(path, 'WIDGETS')
        _webui = read_json(path, 'WEBUI')
        return {**_environment, **_widgets, **_webui}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}

def is_package_installed(package_name):
    try:
        subprocess.run(["npm", "ls", "-g", package_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def get_public_ip(version='ipv4'):
    try:
        url = f'https://api64.ipify.org?format=json&{version}=true'
        response = requests.get(url)
        return response.json().get('ip', 'N/A')
    except Exception as e:
        print(f"Error getting public {version} address:", e)
        return None

def update_config_paths(config_path, paths_to_check):
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config_data = json.load(file)
        for key, expected_value in paths_to_check.items():
            if key in config_data and config_data[key] != expected_value:
                sed_command = f"sed -i 's|\"{key}\": \".*\"|\"{key}\": \"{expected_value}\"|' {config_path}"
                os.system(sed_command)

# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)

print('Please Wait...')

# Get public IP address
public_ipv4 = read_json(SETTINGS_PATH, "ENVIRONMENT.public_ip", None)
if not public_ipv4:
    public_ipv4 = get_public_ip(version='ipv4')
    update_json(SETTINGS_PATH, "ENVIRONMENT.public_ip", public_ipv4)

tunnel_port = 1834
tunnel = Tunnel(tunnel_port)
tunnel.logger.setLevel(logging.DEBUG)

# Define tunnel commands
tunnels = [
    {
        "command": f"cl tunnel --url localhost:{tunnel_port}",
        "name": "cl",
        "pattern": re.compile(r"[\w-]+\.trycloudflare\.com")
    },
    {
        "command": f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{tunnel_port} a.pinggy.io",
        "name": "pinggy",
        "pattern": re.compile(r"[\w-]+\.a\.free\.pinggy\.link")
    }
]

lt_tunnel = is_package_installed('localtunnel')

if lt_tunnel:
    tunnels.append({
        "command": f"lt --port {tunnel_port}",
        "name": "lt",
        "pattern": re.compile(r"[\w-]+\.loca\.lt"),
        "note": "Password : " + "\033[32m" + public_ipv4 + "\033[0m" + " rerun cell if 404 error."
    })

if zrok_token:
    os.system(f'zrok enable {zrok_token} &> /dev/null')
    tunnels.append({
        "command": f"zrok share public http://localhost:{tunnel_port}/ --headless",
        "name": "zrok",
        "pattern": re.compile(r"[\w-]+\.share\.zrok\.io")
    })

# Add tunnels to the tunnel instance
for tunnel_info in tunnels:
    tunnel.add_tunnel(**tunnel_info)

clear_output()

# Update configuration paths
paths_to_check = {
    "tagger_hf_cache_dir": f"{WEBUI}/models/interrogators/",
    "ad_extra_models_dir": f"{WEBUI}/models/adetailer/",
    "sd_checkpoint_hash": "",
    "sd_model_checkpoint": "",
    "sd_vae": "None"
}
update_config_paths(f'{WEBUI}/config.json', paths_to_check)

print(f"🔧 WebUI: \033[34m{UI} \033[0m")

# Launching with tunnel
if __name__ == "__main__":
    with tunnel:
        os.chdir(WEBUI)
        commandline_arguments += f' --port={tunnel_port}'

        if ENV_NAME != "Google Colab":
            commandline_arguments += f' --encrypt-pass={tunnel_port} --api'

        if UI != 'ComfyUI':
            get_ipython().system(f'COMMANDLINE_ARGS="{commandline_arguments}" python launch.py')
        else:
            get_ipython().system('pip install -r requirements.txt')
            get_ipython().system(f'python main.py {commandline_arguments}')

    # Print session duration
    timer = float(open(f'{WEBUI}/static/timer.txt', 'r').read())
    time_since_start = str(timedelta(seconds=time.time() - timer)).split('.')[0]
    print(f"\n⌚️ You have been conducting this session for - \033[33m{time_since_start}\033[0m")

    if zrok_token:
        os.system('zrok disable &> /dev/null')