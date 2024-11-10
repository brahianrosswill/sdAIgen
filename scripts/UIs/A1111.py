# ~ A1111.py | by: ANXETY ~

from json_utils import read_json, update_json   # JSON (main)

from IPython.display import clear_output
from IPython.utils import capture
from pathlib import Path
import shutil
import os

# Constants
UI = 'A1111'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

REPO_ZIP_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"

BRANCH = read_json(SETTINGS_PATH, 'ENVIRONMENT.branch')

os.chdir(HOME)

# ==================== FILE OPERATIONS ====================

def remove_directory(directory_path):
    """Removes a directory if it exists."""
    if directory_path and os.path.exists(directory_path):
        try:
            shutil.rmtree(directory_path)
        except Exception:
            get_ipython().system(f'rm -rf {directory_path}')

# ==================== WEB UI OPERATIONS ====================

def download_configuration():
    cfgs = [
        f'https://raw.githubusercontent.com/anxety-solo/sdAIgen/refs/heads/{BRANCH}/__configs__/{UI}/config.json',
        f'https://raw.githubusercontent.com/anxety-solo/sdAIgen/refs/heads/{BRANCH}/__configs__/{UI}/ui-config.json',
        f'https://raw.githubusercontent.com/anxety-solo/sdAIgen/refs/heads/{BRANCH}/__configs__/styles.csv',
        f'https://raw.githubusercontent.com/anxety-solo/sdAIgen/refs/heads/{BRANCH}/__configs__/user.css'
    ]

    for url in cfgs:
        filename = os.path.join(WEBUI, os.path.basename(url))
        command = f"curl -sLo {filename} {url}"

        os.system(command)

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