from json_utils import read_json, save_json, update_json

from pathlib import Path
import os

# Constants
HOME = Path.home()
SETTINGS_PATH = HOME / 'ANXETY' / 'settings.json'
SCR_PATH = Path(HOME / 'ANXETY')

def update_current_webui(current_value):
    # Read the current and latest stored values
    current_stored_value = read_json(SETTINGS_PATH, 'WEBUI.current')
    latest_value = read_json(SETTINGS_PATH, 'WEBUI.latest', None)

    # If there is no latest value, save the current value as the latest
    if latest_value is None:
        save_json(SETTINGS_PATH, 'WEBUI.current', current_value)
        save_json(SETTINGS_PATH, 'WEBUI.latest', current_value)
    else:
        # If the current value differs from the stored current value
        if current_stored_value != current_value:
            # Save the current stored value as the latest
            if current_stored_value is not None:
                save_json(SETTINGS_PATH, 'WEBUI.latest', current_stored_value)
            # Update the current value
            update_json(SETTINGS_PATH, 'WEBUI.current', current_value)

    # Save the web UI path
    save_json(SETTINGS_PATH, 'WEBUI.webui_path', f'{HOME}/{current_value}')

    # Call the function to set web UI paths
    _set_webui_paths(current_value)

def _set_webui_paths(ui):
    webui_paths = {
        'A1111': ('A1111', 'extensions', 'embeddings', 'VAE', 'Stable-diffusion', 'Lora', 'ESRGAN'),
        'ReForge': ('ReForge', 'extensions', 'embeddings', 'VAE', 'Stable-diffusion', 'Lora', 'ESRGAN'),
        'ComfyUI': ('ComfyUI', 'custom_nodes', 'embeddings', 'vae', 'checkpoints', 'loras', 'upscale_models')
    }
    if ui not in webui_paths:
        return

    webui_name, extension, embed, vae, checkpoint, lora, upscale = webui_paths[ui]

    webui = HOME / webui_name
    models = webui / 'models'

    embeddings = models / embed if ui == 'ComfyUI' else webui / embed
    controlnets = 'controlnet' if ui == 'ComfyUI' else 'ControlNet'
    webui_output = webui / 'output' if ui == 'ComfyUI' else 'outputs'

    paths = {
        # 'models': str(models),
        'model_dir': str(models / checkpoint),
        'vae_dir': str(models / vae),
        'lora_dir': str(models / lora),
        'embed_dir': str(embeddings),
        'extension_dir': str(webui / extension),
        'control_dir': str(models / controlnets),
        'upscale_dir': str(models / upscale),
        'adetailer_dir': str(models / 'adetailer'),
        'output_dir': str(webui_output)
    }

    update_json(SETTINGS_PATH, 'WEBUI', paths)

def handle_colab_timer(webui_path, timer_webui):
    timer_file_path = os.path.join(webui_path, 'static', 'timer.txt')
    
    os.makedirs(os.path.dirname(timer_file_path), exist_ok=True)

    if not os.path.exists(timer_file_path):
        with open(timer_file_path, 'w') as timer_file:
            timer_file.write(str(timer_webui))
    else:
        with open(timer_file_path, 'r') as timer_file:
            timer_webui = float(timer_file.read())

    return timer_webui