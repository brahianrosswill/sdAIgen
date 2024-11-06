# ~ setup.py | by: ANXETY ~

from IPython.display import display, HTML, clear_output
from urllib.parse import urljoin
from pathlib import Path
from tqdm import tqdm
import importlib
import json
import time
import sys
import os

import argparse 

# Constants
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

# ================ BEAUTIFUL TEXT :3 ================
def display_info(env, scr_folder):
    content = f"""
    <div id="text-container">
      <span>A</span>
      <span>N</span>
      <span>X</span>
      <span>E</span>
      <span>T</span>
      <span>Y</span>
      <span>&nbsp;</span>
      <span>S</span>
      <span>D</span>
      <span>-</span>
      <span>W</span>
      <span>E</span>
      <span>B</span>
      <span>U</span>
      <span>I</span>
      <span>&nbsp;</span>
      <span>V</span>
      <span>2</span>
    </div>

    <div id="message-container">
      <span>Готово! Теперь вы можете запустить ячейки ниже. ☄️</span>
      <span>Среда выполнения: <span class="env">{env}</span></span>
      <span>Расположение файлов: <span class="files-location">{scr_folder}</span></span>
    </div>

    <style>
    @import url('https://fonts.googleapis.com/css2?family=Righteous&display=swap');

    #text-container, #message-container {{
      display: flex;
      flex-direction: column;
      height: auto;
      font-family: "Righteous", sans-serif;
      margin: 0;
      padding: 5px 0;
      user-select: none;
    }}

    #text-container {{
      display: flex;
      flex-direction: row;
      align-items: center;
    }}

    #text-container > span {{
      font-size: 4vw;
      display: inline-block;
      color: #FF7A00;
      opacity: 0;
      transform: translateY(-50px);
      filter: blur(3px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    #text-container.loaded > span {{
      color: #FFFFFF;
      opacity: 1;
      transform: translateY(0);
      filter: blur(0);
    }}

    #message-container > span {{
      font-size: 2vw;
      color: #FF7A00;
      opacity: 0;
      transform: translateY(30px);
      filter: blur(3px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    #message-container.loaded > span {{
      color: #FFFFFF;
      opacity: 1;
      transform: translateY(0);
      filter: blur(0);
    }}

    .env {{
      color: #FFA500;
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    .files-location {{
      color: #FF99C2;
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}
    </style>

    <script>
    const textContainer = document.getElementById('text-container');
    const messageContainer = document.getElementById('message-container');
    const textSpans = textContainer.querySelectorAll('span');
    const messageSpans = messageContainer.querySelectorAll('span');

    // Set transition delay for each span in the text container
    textSpans.forEach((span, index) => {{
      span.style.transitionDelay = `${{index * 25}}ms`;
    }});

    // Set transition delay for each span in the message container
    messageSpans.forEach((span, index) => {{
      span.style.transitionDelay = `${{index * 50}}ms`;
    }});


    // Set a timeout to add the 'loaded' class to both containers after a short delay
    setTimeout(() => {{
      textContainer.classList.add('loaded');
      messageContainer.classList.add('loaded');
    }}, 250);
    </script>
    """

    display(HTML(content))

# ==================== FUNCTIONS ====================

def detect_environment():
    environments = {
        'COLAB_GPU': 'Google Colab',
        'KAGGLE_URL_BASE': 'Kaggle'
    }
    for env_var, name in environments.items():
        if env_var in os.environ:
            return name
    raise EnvironmentError(f"Unsupported runtime environment. Supported: {', '.join(environments.values())}")

def _clear_module_cache(modules_folder):
    for module_name in list(sys.modules.keys()):
        module = sys.modules[module_name]
        if hasattr(module, '__file__') and module.__file__ and module.__file__.startswith(str(modules_folder)):
            del sys.modules[module_name]
    importlib.invalidate_caches()

def setup_module_folder(scr_folder):
    _clear_module_cache(scr_folder)

    modules_folder = scr_folder / "modules"
    modules_folder.mkdir(parents=True, exist_ok=True)
    if str(modules_folder) not in sys.path:
        sys.path.append(str(modules_folder))

def save_environment_to_json(data, scr_folder):
    file_path = scr_folder / 'settings.json'
    existing_data = {}

    if file_path.exists():
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)

    existing_data.update(data)

    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

def _get_start_timer():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'r') as f:
            settings = json.load(f)
            start_timer = settings.get('ENVIRONMENT', {}).get('start_timer')
            return start_timer

    return int(time.time() - 5)

def create_environment_data(env, scr_folder, lang):
    scr_folder.mkdir(parents=True, exist_ok=True)   # create main dir
    install_deps = 'xformers' in sys.modules

    # Setup Start Time
    start_timer = _get_start_timer()

    return {
        'ENVIRONMENT': {
            'lang': lang,
            'env_name': env,
            'install_deps': install_deps,
            'home_path': str(scr_folder.parent),
            'scr_path': str(scr_folder),
            'start_timer': start_timer,
            'public_ip': ''
        }
    }

def _process_files(scr_path, files_dict, branch, parent_folder=''):
    repo='sdAIgen'    # waduh~
    file_list = []

    for folder, contents in files_dict.items():
        folder_path = scr_path / parent_folder / folder
        os.makedirs(folder_path, exist_ok=True)

        if isinstance(contents, list):
            for file in contents:
                file_url = urljoin(f"https://raw.githubusercontent.com/anxety-solo/{repo}/{branch}/", f"{parent_folder}{folder}/{file}")
                # print(file_url)
                file_path = folder_path / file
                file_list.append((file_url, file_path))

        elif isinstance(contents, dict):
            file_list.extend(_process_files(scr_path, contents, branch, parent_folder + folder + '/'))

    return file_list

def download_files(scr_path, lang, branch):
    files_dict = {
        'CSS': [
            'main-widgets.css',
            'download-result.css',
            'auto-cleaner.css'
        ],
        'JS': ['main-widgets.js'],
        'modules': [
            'json_utils.py',
            'webui_utils.py',
            'widget_factory.py'
        ],
        'scripts': {
            lang: [
            	# UIs
                f'A1111-{lang}.py',
                f'ReForge-{lang}.py',
                f'ComfyUI-{lang}.py',
                # ---
                f'widgets-{lang}.py',		# Main Widgets
                f'downloading-{lang}.py' 	# Main Downloads (Repo, Models, other...)
            ],
            '': [
            	'launch.py',			# Lauch WebUI
                'auto-cleaner.py',		# Clear Models
                # -Others Scripts-
                'download-result.py',
                'models-data.py',
                'xl-models-data.py'
            ]
        }
    }

    file_list = _process_files(scr_path, files_dict, branch)

    for file_url, file_path in tqdm(file_list, desc="Downloading files", unit="file"):
        os.system(f'wget -q {file_url} -O {file_path}')

    clear_output()

# ======================= MAIN ======================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download script for ANXETY.')
    parser.add_argument('--lang', type=str, default='en', help='Language to be used (default: en)')
    parser.add_argument('--branch', type=str, default='main', help='Branch to download files from (default: main)')
    args = parser.parse_args()

    lang = args.lang
    branch = args.branch
    # ---

    env = detect_environment()

    download_files(SCR_PATH, lang, branch)          # download scripts files
    setup_module_folder(SCR_PATH)                   # setup main dir -> modeules

    env_data = create_environment_data(env, SCR_PATH, lang)
    save_environment_to_json(env_data, SCR_PATH)

    display_info(env, SCR_PATH)                     # display info text :3