# ~ ComfyUI.py | by: ANXETY ~

from json_utils import read_json, update_json   # JSON (main)

from IPython.display import clear_output
from IPython.utils import capture
from pathlib import Path
import shutil
import os

# Constants
UI = 'ComfyUI'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

REPO_ZIP_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
BRANCH = read_json(SETTINGS_PATH, 'ENVIRONMENT.branch')

EXTS = read_json(SETTINGS_PATH, 'WEBUI.extension_dir')

os.chdir(HOME)

# ==================== WEB UI OPERATIONS ====================

def _download_file(url, directory, filename):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    command = f"curl -sLo {file_path} {url}"
    os.system(command)

def _clone_repository():
    extensions_list = [
        "git clone --depth 1 --recursive https://github.com/ssitu/ComfyUI_UltimateSDUpscale",
        "git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager",
        "git clone --depth 1 https://github.com/pythongosssss/ComfyUI-Custom-Scripts"
    ]
    os.chdir(EXTS)

    for command in extensions_list:
        os.system(command)

def download_configuration():
    _clone_repository()

def unpack_webui():
    """Clones the web UI repository."""
    with capture.capture_output():
        zip_path = f"{SCR_PATH}/{UI}.zip"
        get_ipython().system(f'aria2c --console-log-level=error -c -x 16 -s 16 -k 1M {REPO_ZIP_URL} -d {SCR_PATH} -o {UI}.zip')
        get_ipython().system(f'unzip -q -o {zip_path} -d {WEBUI}')
        get_ipython().system(f'rm -rf {zip_path}')

# ==================== MAIN CODE ====================

if __name__ == "__main__":
    unpack_webui()
    download_configuration()