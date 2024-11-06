# ~ A1111.py | by: ANXETY ~

from json_utils import read_json, update_json   # JSON (main)
from webui_utils import handle_colab_timer      # WEBUI

from IPython.display import clear_output
from IPython.utils import capture
from datetime import timedelta
from pathlib import Path
import shutil
import time
import os

# Constants
UI = 'A1111'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

REPO_ZIP_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"

# ==================== INITIALIZATION ====================

def initialize():
    """Initialize settings and change working directory."""
    os.chdir(HOME)
    start_timer = read_json(SETTINGS_PATH, 'ENVIRONMENT.start_timer')
    return start_timer

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
    start_install = time.time()
    print(f"⌚ Распаковка Stable Diffusion... | WEBUI: \033[34m{UI}\033[0m", end='')

    with capture.capture_output():
        zip_path = f"{SCR_PATH}/repo.zip"
        get_ipython().system(f'aria2c --console-log-level=error -c -x 16 -s 16 -k 1M {REPO_ZIP_URL} -d {SCR_PATH} -o repo.zip')
        get_ipython().system(f'unzip -q -o {zip_path} -d {WEBUI}')
        get_ipython().system(f'rm -rf {zip_path}')

    handle_colab_timer(WEBUI, start_timer)

    install_time = time.time() - start_install
    minutes, seconds = divmod(int(install_time), 60)
    print(f"\r🚀 Распаковка Завершена! За {minutes:02}:{seconds:02} ⚡" + " "*15)

# ==================== MAIN CODE ====================

if __name__ == "__main__":
    start_timer = initialize()
    current_UI = read_json(SETTINGS_PATH, "WEBUI.current")
    # latest_UI = read_json(SETTINGS_PATH, "WEBUI.latest")

    if not os.path.exists(WEBUI):
        unpack_webui()
        download_configuration()
    else:
        print(f"🔧 Текущий WebUI: \033[34m{current_UI} \033[0m")
        print("🚀 Распаковка завершена. Пропуск. ⚡")

        timer_colab = handle_colab_timer(WEBUI, start_timer)
        elapsed_time = str(timedelta(seconds=time.time() - timer_colab)).split('.')[0]

        print(f"⌚️ Вы проводите эту сессию в течение - \033[33m{elapsed_time}\033[0m")