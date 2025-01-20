# ~ download.py | by ANXETY ~

from json_utils import read_json, save_json, update_json    # JSON (main)
from webui_utils import handle_setup_timer                  # WEBUI
from CivitaiAPI import CivitAiAPI                           # CivitAI API
from Manager import m_download                              # Every Download

from IPython.display import clear_output
from IPython.utils import capture
from urllib.parse import urlparse
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import zipfile
import shlex
import time
import json
import sys
import re
import os


CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# Constants
HOME = Path.home()
VENV = HOME / 'venv'
SCR_PATH = Path(HOME / 'ANXETY')
SCRIPTS = SCR_PATH / 'scripts'
SETTINGS_PATH = SCR_PATH / 'settings.json'

LANG = read_json(SETTINGS_PATH, 'ENVIRONMENT.lang')
ENV_NAME = read_json(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = read_json(SETTINGS_PATH, 'WEBUI.current')
WEBUI = read_json(SETTINGS_PATH, 'WEBUI.webui_path')


# ============ loading settings V5 =============
def load_settings(path):
    """Load settings from a JSON file."""
    try:
        return {
            **read_json(path, 'ENVIRONMENT'),
            **read_json(path, 'WIDGETS'),
            **read_json(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}

# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)

# ================ LIBRARIES | VENV ================
def setup_venv():
    """The main function to customize the virtual environment."""
    url = "https://huggingface.co/NagisaNao/ANXETY/resolve/main/venv-torch251-cu121-Kfac.tar.lz4"
    fn = Path(url).name

    m_download(f'{url} {HOME} {fn}')

    # Installing dependencies
    install_commands = []
    if ENV_NAME == 'Google Colab':
        """
        # I agree with the author of the correction here ;3
        for blyat in [
            'sudo ln -sf /usr/bin/python3.10 /usr/local/bin/python',
            'sudo ln -sf /usr/bin/python3.10 /usr/bin/python3',
            'sudo rm -rf /usr/local/lib/python3.10',
            'sudo ln -sf /usr/local/lib/python3.11 /usr/local/lib/python3.10'
        ]:
            ipySys(blyat)
        """

        install_commands = ["apt -y install python3.10-venv"]
    else:
        install_commands = ["pip install ipywidgets jupyterlab_widgets --upgrade"]
        ipySys('rm -f /usr/lib/python3.10/sitecustomize.py')

    install_commands.extend(["apt -y install lz4 pv"])
    
    for cmd in install_commands:
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Unpacking and cleaning
    CD(HOME)
    ipySys(f'pv {fn} | lz4 -d | tar xf -')
    Path(fn).unlink()

    ipySys(f'rm -rf {VENV}/bin/pip* {VENV}/bin/python*')

    # Create a virtual environment
    python_command = 'python3.10' if ENV_NAME == 'Google Colab' else 'python3'    # BAN!
    venv_commands = [
    #     f'python3 -m venv {VENV}',
        f'{python_command} -m venv {VENV}',
        f'{VENV}/bin/python3 -m pip install -U --force-reinstall pip',
        f'{VENV}/bin/python3 -m pip install ipykernel',
        f'{VENV}/bin/python3 -m pip uninstall -y ngrok pyngrok'
    ]
    if UI in ['Forge', 'ComfyUI']:
        venv_commands.append(f'{VENV}/bin/python3 -m pip uninstall -y transformers')

    for cmd in venv_commands:
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def install_packages(install_lib):
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\r[{index}/{len(install_lib)}] \033[32m>>\033[0m Installing \033[33m{package}\033[0m..." + " "*35, end='')
        result = subprocess.run(install_cmd, shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"\n\033[31mError installing {package}: {result.stderr.decode()}\033[0m")

if not read_json(SETTINGS_PATH, 'ENVIRONMENT.install_deps'):
    install_lib = {
        ## libs
        "aria2": "pip install aria2",
        "gdown": "pip install gdown",
        # "pv": "apt -y install pv",
        ## tunnels
        "localtunnel": "npm install -g localtunnel",
        "cloudflared": "wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod +x /usr/bin/cl",
        "zrok": "wget -qO zrok_0.4.44_linux_amd64.tar.gz https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz; tar -xzf zrok_0.4.44_linux_amd64.tar.gz -C /usr/bin; rm -f zrok_0.4.44_linux_amd64.tar.gz",
        "ngrok": "wget -qO ngrok-v3-stable-linux-amd64.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz; tar -xzf ngrok-v3-stable-linux-amd64.tgz -C /usr/bin; rm -f ngrok-v3-stable-linux-amd64.tgz" 
    }

    # Main Deps
    print("💿 Installing the libraries, this will take some time.")
    install_packages(install_lib)
    clear_output()

    # VENV
    print("♻️ Installing VENV, this will take some time...")
    setup_venv()
    clear_output()

    # update settings
    update_json(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

    print("🍪 The libraries and VENV are installed!")
    time.sleep(2)
    clear_output()

# =================== WEBUI ===================
start_timer = read_json(SETTINGS_PATH, 'ENVIRONMENT.start_timer')

if not os.path.exists(WEBUI):
    start_install = time.time()
    print(f"⌚ Unpacking Stable Diffusion... | WEBUI: \033[34m{UI}\033[0m", end='')

    ipyRun('run', f'{SCRIPTS}/UIs/{UI}.py')
    handle_setup_timer(WEBUI, start_timer)		# Setup timer (for ncpt timer-extensions)

    install_time = time.time() - start_install
    minutes, seconds = divmod(int(install_time), 60)
    print(f"\r🚀 Unpacking is complete! For {minutes:02}:{seconds:02} ⚡" + " "*25)

else:
    print(f"🔧 Current WebUI: \033[34m{UI} \033[0m")
    print("🚀 Unpacking is complete. Pass. ⚡")

    timer_env = handle_setup_timer(WEBUI, start_timer)
    elapsed_time = str(timedelta(seconds=time.time() - timer_env)).split('.')[0]
    print(f"⌚️ You've been conducting this session for - \033[33m{elapsed_time}\033[0m")


## Changes extensions and WebUi
if latest_webui or latest_extensions:
    action = "WebUI and Extensions" if latest_webui and latest_extensions else ("WebUI" if latest_webui else "Extensions")
    print(f"⌚️ Update {action}...", end='')
    with capture.capture_output():
        ipySys('git config --global user.email "you@example.com"')
        ipySys('git config --global user.name "Your Name"')

        ## Update Webui
        if latest_webui:
            CD(WEBUI)
            ipySys('git restore .')
            ipySys('git pull -X theirs --rebase --autostash')

        ## Update extensions
        if latest_extensions:
            ipySys('{\'for dir in \' + WEBUI + \'/extensions/*/; do cd \\"$dir\\" && git reset --hard && git pull; done\'}')          
    print(f"\r✨ Update {action} Completed!")


# === FIXING EXTENSIONS ===
with capture.capture_output():
    # --- Umi-Wildcard ---
    ipySys("sed -i '521s/open=\\(False\\|True\\)/open=False/' {WEBUI}/extensions/Umi-AI-Wildcards/scripts/wildcard_recursive.py  # Closed accordion by default")

## Version switching
if commit_hash:
    print('🔄 Switching to the specified version...', end="")
    with capture.capture_output():
        CD(WEBUI)
        ipySys('git config --global user.email "you@example.com"')
        ipySys('git config --global user.name "Your Name"')
        ipySys('git reset --hard {commit_hash}')
        ipySys('git pull origin {commit_hash}')    # Get last changes in branch
    print(f"\r🔄 Switch complete! Current commit: \033[34m{commit_hash}\033[0m")


# Get XL or 1.5 models list
## model_list | vae_list | controlnet_list
model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
with open(f'{SCRIPTS}/{model_files}') as f:
    exec(f.read())

## Downloading model and stuff | oh~ Hey! If you're freaked out by that code too, don't worry, me too!
print("📦 Downloading models and stuff...", end='')

extension_repo = []
PREFIXES = {
    "model": model_dir,
    "vae": vae_dir,
    "lora": lora_dir,
    "embed": embed_dir,
    "extension": extension_dir,
    "adetailer": adetailer_dir,
    "control": control_dir,
    "upscale": upscale_dir,
    "clip": clip_dir,
    "config": WEBUI
}
for path in PREFIXES.values():
    os.makedirs(path, exist_ok=True)

''' Formatted Info Output '''

def _center_text(text, terminal_width=45):
    padding = (terminal_width - len(text)) // 2
    return f"{' ' * padding}{text}{' ' * padding}"

def format_output(url, dst_dir, file_name, image_url=None, image_name=None, paid_model=None):
    info = _center_text(f"[{file_name.split('.')[0]}]")
    sep_line = '---' * 20

    print(f"\n\033[32m{sep_line}\033[36;1m{info}\033[32m{sep_line}\033[0m")
    print(f"\033[33mURL: \033[0m{url}")
    print(f"\033[33mSAVE DIR: \033[34m{dst_dir}")
    print(f"\033[33mFILE NAME: \033[34m{file_name}\033[0m")
    if 'civitai' in url and image_url:
        print(f"\033[32m[Preview]:\033[0m {image_name} -> {image_url}")
    print()

''' Main Download Code '''

def _STRIP_URL(url):
    """Removes unnecessary parts from the URL for correct downloading."""
    if "huggingface.co" in url:
        url = url.replace('/blob/', '/resolve/')
        if '?' in url:
            url = url.split('?')[0]

    elif 'github.com' in url:
        return url.replace('/blob/', '/raw/')

    return url

def _GET_FILE_NAME(url):
    file_name_match = re.search(r'\[(.*?)\]', url)
    if file_name_match:
        return file_name_match.group(1)

    file_name_parse = urlparse(url)
    if any(domain in file_name_parse.netloc for domain in ["civitai.com", "drive.google.com"]):
        return None

    return Path(file_name_parse.path).name

def _UNPUCK_ZIP():
    """Extracts all ZIP files in the directories specified in PREFIXES."""
    for directory in PREFIXES.values():
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".zip"):
                    zip_path = os.path.join(root, file)
                    extract_path = os.path.splitext(zip_path)[0]
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    os.remove(zip_path)

def _handle_manual_download(link):
    """Handles downloads for URLs with prefixes."""
    url_parts = link.split(':', 1)
    prefix, path = url_parts[0], url_parts[1]

    file_name = _GET_FILE_NAME(path)
    path = re.sub(r'\[.*?\]', '', path)

    if prefix in PREFIXES:
        dir = PREFIXES[prefix]
        if prefix != "extension":
            try:
                manual_download(path, dir, file_name=file_name, prefix=prefix)
            except Exception as e:
                print(f"Error downloading file: {e}")
        else:
            extension_repo.append((path, file_name))

def download(line):
    links = [link.strip() for link in line.split(',') if link.strip()]

    for link in links:
        link = _STRIP_URL(link)

        if any(link.lower().startswith(prefix) for prefix in PREFIXES):
            _handle_manual_download(link)
        else:
            url, dst_dir, file_name = link.split()
            manual_download(url, dst_dir, file_name)

    # Unpacking ZIP files
    _UNPUCK_ZIP()

def manual_download(url, dst_dir, file_name=None, prefix=None):
    clean_url = url
    image_url, image_name = None, None
    if 'civitai' in url:
        civitai = CivitAiAPI(civitai_token)
        data = civitai.fetch_data(url)

        if data is None:
            return    # Terminate the function if no data is received
        if civitai.check_early_access(data):
            return    # Exit if the model requires payment

        # model info
        model_type, file_name = civitai.get_model_info(data, url, file_name)    # model_name -> file_name
        download_url = civitai.get_download_url(data, url)
        clean_url, url = civitai.get_full_and_clean_download_url(download_url)
        image_url, image_name = civitai.get_image_info(data, file_name, model_type)

        # DL PREVIEW IMAGES | CIVITAI
        if image_url and image_name:
            m_download(f"{image_url} {dst_dir} {image_name}")

    elif 'github' in url or 'huggingface.co' in url:
        if file_name and '.' not in file_name:
            file_extension = f"{clean_url.split('/')[-1].split('.', 1)[1]}"
            file_name = f"{file_name}.{file_extension}"
        if not file_name:
            file_name = clean_url.split("/")[-1]

    ## Formatted info output
    format_output(clean_url, dst_dir, file_name, image_url, image_name)

    # Downloading
    # file_path = os.path.join(dst_dir, file_name)
    # if os.path.exists(file_path) and prefix == 'config':
    #     os.remove(file_path)

    m_download(f"{url} {dst_dir} {file_name}", log=True)

''' SubModels - Added URLs '''

# Separation of merged numbers
def split_numbers(num_str, max_num):
    unique_numbers = set()
    nums_str = num_str.replace(',', ' ').strip()

    i = 0
    while i < len(nums_str):
        found = False
        for length in range(2, 0, -1):
            if i + length <= len(nums_str):
                part = int(nums_str[i:i + length])
                if part <= max_num:
                    unique_numbers.add(part)
                    i += length
                    found = True
                    break
        if not found:
            break

    return sorted(unique_numbers)

def add_submodels(selection, num_selection, model_dict, dst_dir):
    if selection == "none":
        return []
    selected_models = []

    if selection == "ALL":
        selected_models = sum(model_dict.values(), [])
    else:
        selected_models.extend(model_dict.get(selection, []))

        max_num = len(model_dict)
        unique_nums = split_numbers(num_selection, max_num)

        for num in unique_nums:
            if 1 <= num <= max_num:
                name = list(model_dict.keys())[num - 1]
                selected_models.extend(model_dict[name])

    unique_models = {}
    for model in selected_models:
        if 'name' not in model and 'huggingface.co' in model['url']:
            model['name'] = os.path.basename(model['url'])
        model['dst_dir'] = dst_dir
        unique_models[model['name']] = model

    return list(unique_models.values())

def handle_submodels(selection, num_selection, model_dict, dst_dir, url):
    submodels = add_submodels(selection, num_selection, model_dict, dst_dir)
    for submodel in submodels:
        if not inpainting_model and "inpainting" in submodel['name']:
            continue
        url += f"{submodel['url']} {submodel['dst_dir']} {submodel['name']}, "
    return url

line = ""
line = handle_submodels(model, model_num, model_list, model_dir, line)
line = handle_submodels(vae, vae_num, vae_list, vae_dir, line)
line = handle_submodels(controlnet, controlnet_num, controlnet_list, control_dir, line)

''' file.txt - added urls '''

def process_file_download(file_url, prefixes, unique_urls):
    files_urls = ""
    current_tag = None

    if file_url.startswith("http"):
        file_url = _STRIP_URL(file_url)
        response = requests.get(file_url)
        lines = response.text.split('\n')
    else:
        with open(file_url, 'r') as file:
            lines = file.readlines()

    for line in lines:
        line = line.strip()

        for prefix in prefixes.keys():
            if f'# {prefix}'.lower() in line.lower():
                current_tag = prefix
                break

        urls = [url.split('#')[0].strip() for url in line.split(',')]
        for url in urls:
            filter_url = url.split('[')[0].strip()    # Take out the unnecessary parts of the URL

            # Check if the URL is unique
            if url.startswith("http") and filter_url not in unique_urls:
                files_urls += f"{current_tag}:{url}, "
                unique_urls.add(filter_url)

    return files_urls

file_urls = ""
unique_urls = set()

if custom_file_urls:
    for custom_files in custom_file_urls.replace(',', '').split():
        if not custom_files.endswith('.txt'):
            custom_files += '.txt'

        try:
            file_urls += process_file_download(custom_files, PREFIXES, unique_urls)
        except FileNotFoundError:
            pass

# URL prefixing
urls = (Model_url, Vae_url, LoRA_url, Embedding_url, Extensions_url, ADetailer_url)
prefixed_urls = [
    f"{prefix}:{url.strip()}"
    for prefix, url in zip(PREFIXES.keys(), urls)
    if url for url in url.replace(',', '').split()
]
line += ", ".join(prefixed_urls) + ", " + file_urls

if detailed_download == "on":
    print("\n\n\033[33m# ====== Detailed Download ====== #\n\033[0m")
    download(line)
    print("\n\033[33m# =============================== #\n\033[0m")
else:
    with capture.capture_output():
        download(line)

print("\r🏁 Download Complete!" + " "*15)


## Install of Custom extensions
def _clone_repository(repo, repo_name, extension_dir):
    """Clones the repository to the specified directory."""
    repo_name = repo_name or repo.split('/')[-1]
    command = f'cd {extension_dir} && git clone --depth 1 --recursive {repo} {repo_name} && cd {repo_name} && git fetch'
    ipySys(command)

extension_type = 'nodes' if UI == 'ComfyUI' else 'extensions'

if extension_repo:
    print(f"✨ Installing custom {extension_type}...", end='')
    with capture.capture_output():
        for repo, repo_name in extension_repo:
            _clone_repository(repo, repo_name, extension_dir)
    print(f"\r📦 Installed '{len(extension_repo)}' custom {extension_type}!")


## List Models and stuff
ipyRun('run', f'{SCRIPTS}/download-result.py')