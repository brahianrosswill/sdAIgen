# ~ ReForge.py | by: ANXETY ~

from json_utils import read_json, update_json   # JSON (main)

from IPython.display import clear_output
from IPython.utils import capture
from pathlib import Path
import shutil
import os

# Constants
UI = 'ReForge'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

REPO_ZIP_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"

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
    pass

def unpack_webui():
    """Clones the web UI repository."""
    with capture.capture_output():
        zip_path = f"{SCR_PATH}/repo.zip"
        get_ipython().system(f'aria2c --console-log-level=error -c -x 16 -s 16 -k 1M {REPO_ZIP_URL} -d {SCR_PATH} -o repo.zip')
        get_ipython().system(f'unzip -q -o {zip_path} -d {WEBUI}')
        get_ipython().system(f'rm -rf {zip_path}')

# ==================== MAIN CODE ====================

if __name__ == "__main__":
    unpack_webui()
    download_configuration()