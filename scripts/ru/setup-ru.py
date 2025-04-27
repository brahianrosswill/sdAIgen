# ~ setup.py | by ANXETY ~

from IPython.display import clear_output
from urllib.parse import urljoin
from pathlib import Path
from tqdm import tqdm
import nest_asyncio
import importlib
import argparse
import asyncio
import aiohttp
import time
import json
import sys
import os


# Constants
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

nest_asyncio.apply()  # Async support for Jupyter


## ======================= DISPLAY =======================

def get_season():
    import datetime
    month = datetime.datetime.now().month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def display_info(env, scr_folder, branch):
    season = get_season()
    season_config = {
        'winter': {
            'bg': 'linear-gradient(180deg, #66666633, transparent)',
            'primary': '#666666',
            'accent': '#ffffff',
            'icon': '❄️'
        },
        'spring': {
            'bg': 'linear-gradient(180deg, #9366b433, transparent)',
            'primary': '#9366b4',
            'accent': '#dbcce6',
            'icon': '🌸'
        },
        'summer': {
            'bg': 'linear-gradient(180deg, #ffe76633, transparent)',
            'primary': '#ffe766',
            'accent': '#fff7cc',
            'icon': '🌴'
        },
        'autumn': {
            'bg': 'linear-gradient(180deg, #ff8f6633, transparent)',
            'primary': '#ff8f66',
            'accent': '#ffd9cc',
            'icon': '🍁'
        }
    }
    config = season_config.get(season, season_config['winter'])

    CONTENT = f"""
    <div class="season-container">
      <div class="text-container">
        <span>{config['icon']}</span>
        <span>A</span><span>N</span><span>X</span><span>E</span><span>T</span><span>Y</span>
        <span>&nbsp;</span>
        <span>S</span><span>D</span><span>-</span><span>W</span><span>E</span><span>B</span><span>U</span><span>I</span>
        <span>&nbsp;</span>
        <span>V</span><span>2</span>
        <span>{config['icon']}</span>
      </div>

      <div id="message-container">
        <span>Готово! Теперь вы можете запустить ячейки ниже. ☄️</span>
        <span>Среда выполнения: <span class="env">{env}</span></span>
        <span>Расположение файлов: <span class="files-location">{scr_folder}</span></span>
        <span>Текущая ветка: <span class="branch">{branch}</span></span>
      </div>
    </div>
    """

    STYLE = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Righteous&display=swap');

    .season-container {{
      position: relative;
      margin: 0 10px !important;
      padding: 20px !important;
      border-radius: 15px;
      margin: 10px 0;
      overflow: hidden;
      min-height: 200px;
      background: {config['bg']};
      border-top: 2px solid {config['primary']};
    }}

    .text-container {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      gap: 0.5em;
      font-family: 'Righteous', cursive;
      margin-bottom: 1em;
    }}

    .text-container span {{
      font-size: 2.5rem;
      color: {config['primary']};
      opacity: 0;
      transform: translateY(-20px);
      filter: blur(4px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    .text-container.loaded span {{
      opacity: 1;
      transform: translateY(0);
      filter: blur(0);
      color: {config['accent']};
    }}

    .message-container {{
      font-family: 'Righteous', cursive;
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 0.5em;
    }}

    .message-container span {{
      font-size: 1.2rem;
      color: {config['primary']};
      opacity: 0;
      transform: translateY(20px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    .message-container.loaded span {{
      opacity: 1;
      transform: translateY(0);
      color: {config['accent']};
    }}

    .env {{ color: #FFA500 !important; }}
    .files-location {{ color: #FF99C2 !important; }}
    .branch {{ color: #16A543 !important; }}
    </style>
    """

    SNOW_SCRIPT = """
    <script>
    (function() {
      const style = document.createElement('style');
      style.innerHTML = `
        .snowflake {
          position: absolute;
          background-color: white;
          border-radius: 50%;
          box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
          pointer-events: none;
          opacity: 0.8;
          will-change: transform, opacity;
        }
      `;
      document.head.appendChild(style);

      function clearSnowflakes() {
        document.querySelectorAll('.snowflake').forEach(s => s.remove());
      }

      function createSnowflake() {
        const container = document.querySelector('.season-container');
        const snowflake = document.createElement('div');
        snowflake.className = 'snowflake';

        const size = Math.random() * 5 + 3;
        snowflake.style.width = `${size}px`;
        snowflake.style.height = `${size}px`;

        const containerRect = container.getBoundingClientRect();
        snowflake.style.left = `${Math.random() * (containerRect.width - size)}px`;
        snowflake.style.top = `-${size}px`;

        const opacity = Math.random() * 0.4 + 0.1;
        snowflake.style.opacity = opacity;

        const angle = (Math.random() * 50 - 25) * (Math.PI / 180);
        const horizontal = Math.sin(angle) * (containerRect.height / 2);
        const vertical = Math.cos(angle) * (containerRect.height + 10);

        snowflake.animate([
          { transform: `translate(0, 0)`, opacity: 1 },
          { transform: `translate(${horizontal}px, ${vertical}px)`, opacity: 0 }
        ], {
          duration: (Math.random() * 3 + 2) * 1000,
          easing: 'linear',
          fill: 'forwards'
        });

        container.appendChild(snowflake);
        setTimeout(() => snowflake.remove(), 5000);
      }

      clearSnowflakes();
      setInterval(createSnowflake, 50);

      // Text animation
      const textContainer = document.querySelector('.text-container');
      const messageContainer = document.querySelector('.message-container');
      const textSpans = textContainer.querySelectorAll('span');
      const messageSpans = messageContainer.querySelectorAll('span');

      textSpans.forEach((span, index) => {
        span.style.transitionDelay = `${index * 25}ms`;
      });

      messageSpans.forEach((span, index) => {
        span.style.transitionDelay = `${index * 50}ms`;
      });

      setTimeout(() => {
        textContainer.classList.add('loaded');
        messageContainer.classList.add('loaded');
      }, 250);
    })();
    </script>
    """

    display(HTML(CONTENT + STYLE + SNOW_SCRIPT))


# ===================== UTILITIES (JSON/FILE OPERATIONS) =====================

def key_exists(filepath, key=None, value=None):
    """Check key/value in JSON file."""
    if not filepath.exists():
        return False
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return False

    if key:
        keys = key.split('.')
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return False
        return (data == value) if value else True
    return False

def save_environment_to_json(SETTINGS_PATH, data):
    """Save environment data to a JSON file."""
    existing_data = {}

    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, 'r') as json_file:
            existing_data = json.load(json_file)

    existing_data.update(data)

    with open(SETTINGS_PATH, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

def get_start_timer():
    """Get the start timer from settings or default to current time minus 5 seconds."""
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, 'r') as f:
            settings = json.load(f)
            return settings.get('ENVIRONMENT', {}).get('start_timer', int(time.time() - 5))
    return int(time.time() - 5)


# ===================== ENVIRONMENT SETUP =====================

def detect_environment():
    """Detect runtime environment."""
    envs = {'COLAB_GPU': 'Google Colab', 'KAGGLE_URL_BASE': 'Kaggle'}
    for var, name in envs.items():
        if var in os.environ:
            return name
    raise EnvironmentError(f"Unsupported environment. Supported: {', '.join(envs.values())}")

def get_fork_info(fork_arg):
    """Parse fork argument into user/repo."""
    if not fork_arg:
        return 'anxety-solo', 'sdAIgen'
    parts = fork_arg.split('/', 1)
    return parts[0], (parts[1] if len(parts) > 1 else 'sdAIgen')

def create_environment_data(env, scr_folder, lang, fork_user, fork_repo, branch):
    """Create a dictionary with environment data."""
    install_deps = key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)
    start_timer = get_start_timer()

    return {
        'ENVIRONMENT': {
            'lang': lang,
            'fork_user': fork_user,
            'fork_repo': fork_repo,
            'branch': branch,
            'env_name': env,
            'install_deps': install_deps,
            'home_path': str(scr_folder.parent),
            'venv_path': str(scr_folder.parent / 'venv'),
            'scr_path': str(scr_folder),
            'start_timer': start_timer,
            'public_ip': ''
        }
    }


# ===================== DOWNLOAD LOGIC =====================

def generate_file_list(structure, base_url, base_path):
    """Generate flat list of (url, path) from nested structure"""
    def walk(struct, path_parts):
        items = []
        for key, value in struct.items():
            current_path = [*path_parts, key] if key else path_parts
            if isinstance(value, dict):
                items.extend(walk(value, current_path))
            else:
                url_path = '/'.join(current_path)
                for file in value:
                    url = f"{base_url}/{url_path}/{file}" if url_path else f"{base_url}/{file}"
                    file_path = base_path / '/'.join(current_path) / file
                    items.append((url, file_path))
        return items

    return walk(structure, [])

async def download_file(session, url, path):
    """Download and save single file"""
    async with session.get(url) as resp:
        resp.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(await resp.read())

async def download_files_async(scr_path, lang, fork_user, fork_repo, branch):
    """Main download executor"""
    files_structure = {
        'CSS': ['main-widgets.css', 'download-result.css', 'auto-cleaner.css'],
        'JS': ['main-widgets.js'],
        'modules': ['json_utils.py', 'webui_utils.py', 'widget_factory.py', 
                   'TunnelHub.py', 'CivitaiAPI.py', 'Manager.py'],
        'scripts': {
            'UIs': ['A1111.py', 'ComfyUI.py', 'Forge.py', 'ReForge.py', 'SD-UX.py'],
            lang: [f"widgets-{lang}.py", f"downloading-{lang}.py"],
            '': ['launch.py', 'auto-cleaner.py', 'download-result.py', 
                '_models-data.py', '_xl-models-data.py']
        }
    }

    base_url = f"https://raw.githubusercontent.com/{fork_user}/{fork_repo}/{branch}"
    file_list = generate_file_list(files_structure, base_url, scr_path)

    async with aiohttp.ClientSession() as session:
        tasks = [download_file(session, url, path) for url, path in file_list]

        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Downloading files", unit="file"):
            await task

    clear_output()


# ===================== MAIN EXECUTION =====================

async def main_async(args=None):
    """Entry point."""
    parser = argparse.ArgumentParser(description='ANXETY Download Manager')
    parser.add_argument('-l', '--lang', type=str, default='en', help='Language to be used (default: en)')
    parser.add_argument('-b', '--branch', type=str, default='main', help='Branch to download files from (default: main)')
    parser.add_argument('-f', '--fork', type=str, default=None, help='Specify project fork (user or user/repo)')
    parser.add_argument('-s', '--skip-download', action='store_true', help='Skip downloading files and just update the directory and modules')

    args, _ = parser.parse_known_args(args)

    env = detect_environment()
    user, repo = get_fork_info(args.fork)   # gitLogin , gitRepoName

    if not args.skip_download:
        await download_files_async(SCR_PATH, args.lang, user, repo, args.branch)    # download scripts files

    env_data = create_environment_data(env, SCR_PATH, args.lang, user, repo, args.branch)
    save_environment_to_json(SETTINGS_PATH, env_data)

    display_info(env, SCR_PATH, args.branch)    # display info text

if __name__ == '__main__':
    asyncio.run(main_async())