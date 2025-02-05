# ~ launch.py | by ANXETY ~

from TunnelHub import Tunnel    # Tunneling
import json_utils as js         # JSON

from IPython.display import clear_output
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import logging
import shlex
import time
import json
import yaml
import os
import re


CD = os.chdir
ipySys = get_ipython().system

# Constants
HOME = Path.home()
VENV = HOME / 'venv'
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = js.read(SETTINGS_PATH, 'WEBUI.webui_path')

# USER VENV | python
py = Path(VENV) / 'bin/python3'


## ================ loading settings V5 ==================
def load_settings(path):
    """Load settings from a JSON file."""
    try:
        return {
            **js.read(path, 'ENVIRONMENT'),
            **js.read(path, 'WIDGETS'),
            **js.read(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}
        
# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)

## ======================= Other =========================

def is_package_installed(package_name):
    """Check if a package is installed globally using npm."""
    try:
        subprocess.run(["npm", "ls", "-g", package_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def get_public_ip(version='ipv4'):
    """Retrieve the public IP address."""
    try:
        url = f'https://api64.ipify.org?format=json&{version}=true'
        response = requests.get(url)
        return response.json().get('ip', 'N/A')
    except Exception as e:
        print(f"Error getting public {version} address:", e)
        return None

def update_config_paths(config_path, paths_to_check):
    """Update configuration paths in the specified JSON config file."""
    for key, expected_value in paths_to_check.items():
        if js.key_exists(config_path, key):
            js.update(config_path, key, expected_value)
        else:
            js.save(config_path, key, expected_value)
             
def trash_checkpoints():
    dirs = ["A1111", "ReForge", "ComfyUI", "Forge"]
    paths = [Path(HOME) / name for name in dirs]

    for path in paths:
        cmd = f"find {path} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

## =================== Tunnel Functions ==================

def check_tunnel_server(url, tunnel_name):
    """Check if the tunnel server is reachable."""
    timeout = 5
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"\033[32m> [SUCCESS]: Tunnel '\033[0m{tunnel_name}\033[32m' is reachable at \033[0m{url}")
            return True
        else:
            error_message = f"returned status code '{response.status_code}'"
    except requests.RequestException as e:
        error_message = f"Unable to access the tunnel: {e}"

    print(f"\033[31m> [ERROR]: Tunnel '\033[0m{tunnel_name}\033[31m' at {url} >> {error_message}\033[0m")
    return False

def _zrok_enable(token):
    zrok_env_path = HOME / '.zrok/environment.json'

    current_token = None
    if zrok_env_path.exists():
        with open(zrok_env_path, 'r') as f:
            current_token = json.load(f).get('zrok_token')

    if current_token != token:
        ipySys('zrok disable &> /dev/null')
    ipySys(f'zrok enable {token} &> /dev/null')

def _ngrok_auth(token):
    yml_ngrok_path = HOME / '.config/ngrok/ngrok.yml'

    current_token = None
    if yml_ngrok_path.exists():
        with open(yml_ngrok_path, 'r') as f:
            current_token = yaml.safe_load(f).get('agent', {}).get('authtoken')

    if current_token != token:
        ipySys(f'ngrok config add-authtoken {token}')
        
def setup_tunnels(tunnel_port, public_ipv4):
    """Setup tunneling commands based on available packages and configurations."""
    tunnels = []
    
    # Check Cloudflared
    cloudflared_url = 'https://www.cloudflare.com'
    if check_tunnel_server(cloudflared_url, "Cloudflared"):
        tunnels.append({
            "command": f"cl tunnel --url localhost:{tunnel_port}",
            "name": "Cloudflared",
            "pattern": re.compile(r"[\w-]+\.trycloudflare\.com")
        })

    # Check LocalTunnel
    if is_package_installed('localtunnel'):
        localtunnel_url = 'https://localtunnel.me'
        if check_tunnel_server(localtunnel_url, "Localtunnel"):
            tunnels.append({
                "command": f"lt --port {tunnel_port}",
                "name": "Localtunnel",
                "pattern": re.compile(r"[\w-]+\.loca\.lt"),
                "note": f"Password : \033[32m{public_ipv4}\033[0m rerun cell if 404 error."
            })

    # Check Pinggy
    pinggy_url = 'https://pinggy.io'
    if check_tunnel_server(pinggy_url, "Pinggy"):
        tunnels.append({
            "command": f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{tunnel_port} a.pinggy.io",
            "name": "Pinggy",
            "pattern": re.compile(r"[\w-]+\.a\.free\.pinggy\.link")
        })

    # Check Zrok
    if zrok_token:
        zrok_url = 'https://status.zrok.io'
        if check_tunnel_server(zrok_url, "Zrok"):
            _zrok_enable(zrok_token)
            tunnels.append({
                "command": f"zrok share public http://localhost:{tunnel_port}/ --headless",
                "name": "Zrok",
                "pattern": re.compile(r"[\w-]+\.share\.zrok\.io")
            })
        
    # Check Ngrok
    if ngrok_token:
        ngrok_url = 'https://ngrok.com'
        if check_tunnel_server(ngrok_url, "Ngrok"):
            _ngrok_auth(ngrok_token)
            tunnels.append({
                "command": f"ngrok http http://localhost:{tunnel_port} --log stdout",
                "name": "Ngrok",
                "pattern": re.compile(r"https://[\w-]+\.ngrok-free\.app")
            })

    return tunnels

## ========================= Main ========================

print('Please Wait...\n')

# Get public IP address
public_ipv4 = js.read(SETTINGS_PATH, "ENVIRONMENT.public_ip", None)
if not public_ipv4:
    public_ipv4 = get_public_ip(version='ipv4')
    js.update(SETTINGS_PATH, "ENVIRONMENT.public_ip", public_ipv4)

tunnel_port = 8188 if UI == 'ComfyUI' else 7860
TunnelingService = Tunnel(tunnel_port)
TunnelingService.logger.setLevel(logging.DEBUG)

# environ
if f'{VENV}/bin' not in os.environ['PATH']:
    os.environ['PATH'] = f'{VENV}/bin:' + os.environ['PATH']
os.environ["PYTHONWARNINGS"] = "ignore"

# Setup tunnels
tunnels = setup_tunnels(tunnel_port, public_ipv4)
for tunnel_info in tunnels:
    TunnelingService.add_tunnel(**tunnel_info)

clear_output()

# Update configuration paths
paths_to_check = {
    "tagger_hf_cache_dir": f"{WEBUI}/models/interrogators/",
    "ad_extra_models_dir": adetailer_dir,
    "sd_checkpoint_hash": "",
    "sd_model_checkpoint": "",
    "sd_vae": "None"
}
update_config_paths(f'{WEBUI}/config.json', paths_to_check)
## Remove '.ipynb_checkpoints' dirs in UI
trash_checkpoints()

# Launching the tunnel
launcher = 'main.py' if UI == 'ComfyUI' else 'launch.py'
password = 'vo9fdxgc0zkvghqwzrlz6rk2o00h5sc7'

# Setup pinggy timer
ipySys(f'echo -n {int(time.time())+(3600+20)} > {WEBUI}/static/timer-pinggy.txt')

with TunnelingService:
    CD(WEBUI)
    commandline_arguments += f' --port={tunnel_port}'
    
    # Default args append
    if UI != 'ComfyUI':
        commandline_arguments += ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
        # NSFW filter for Kaggle
        if ENV_NAME == "Kaggle":
            commandline_arguments += f' --encrypt-pass={password} --api'
    
    ## Launch
    try:
        if UI == 'ComfyUI':
            COMFYUI_SETTINGS_PATH = SCR_PATH / 'ComfyUI.json'
            if check_custom_nodes_deps:
                ipySys(f'{py} install-deps.py')
                clear_output(wait=True)

            if not js.key_exists(COMFYUI_SETTINGS_PATH, 'install_req', True):
                print("Installing dependencies for ComfyUI from requirements.txt...")
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                js.save(COMFYUI_SETTINGS_PATH, 'install_req', True)
                clear_output(wait=True)

        print(f"🔧 WebUI: \033[34m{UI} \033[0m")
        ipySys(f'{py} {launcher} {commandline_arguments}')
    except KeyboardInterrupt:
        pass

# Print session duration
timer = float(open(f'{WEBUI}/static/timer.txt', 'r').read())
time_since_start = str(timedelta(seconds=time.time() - timer)).split('.')[0]
print(f"\n⌚️ You have been conducting this session for - \033[33m{time_since_start}\033[0m")


## Zrok Disable | PARANOYA
if zrok_token:
    ipySys('zrok disable &> /dev/null')
    print('🔐 Zrok tunnel was disabled :3')