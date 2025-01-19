"""
Modified script.

Originated from: https://github.com/gutris1/segsmaker/blob/main/script/SM/nenen88.py
Author: gutris1 https://github.com/gutris1
"""


from json_utils import read_json   # JSON (main)

import os
import re
import sys
import shlex
import zipfile
import requests
import subprocess
from urllib.parse import urlparse, parse_qs
from pathlib import Path


CD = os.chdir

# Constants
HOME = Path.home()
SCR_PATH = Path(HOME / 'ANXETY')
SETTINGS_PATH = SCR_PATH / 'settings.json'

cai_token = read_json(SETTINGS_PATH, 'WIDGETS.civitai_token') or "65b66176dcf284b266579de57fbdc024"
hf_token = read_json(SETTINGS_PATH, 'WIDGETS.huggingface_token') or ""


## ================ Download ================
def m_download(line, log=False, unzip=False):
    """Download files from a comma-separated list of URLs or file paths.
    If a URL points to a .txt file, it reads URLs from that file and processes them."""
    links = [link.strip() for link in line.split(',') if link.strip()]

    if not links:
        if log:
            print("> Missing URL, downloading nothing")
        return

    for link in links:
        url = link[0]
        if url.endswith('.txt') and Path(url).expanduser().is_file():
            with open(Path(url).expanduser(), 'r') as file:
                for line in file:
                    process_download(line, log, unzip)
        else:
            process_download(link, log, unzip)

def process_download(line, log, unzip):
    """Process an individual download line by extracting the URL and determining
    the appropriate method for downloading based on the URL's domain."""
    parts = line.split()
    url = parts[0].replace('\\', '')
    is_special_domain = any(domain in url for domain in ["civitai.com", "huggingface.co", "github.com"])
    is_google_drive = "drive.google.com" in url
    url = clean_url(url)
    current_dir = Path.cwd()

    if not url:
        return

    aria2_command = (
        "aria2c --header='User-Agent: Mozilla/5.0' "
        "--allow-overwrite=true --console-log-level=error --stderr=true "
        "-c -x16 -s16 -k1M -j5"
    )

    if hf_token and "huggingface.co" in url:
        aria2_command += f" --header='Authorization: Bearer {hf_token}'"

    try:
        path, filename = handle_path_and_filename(parts)
        if path:
            path.mkdir(parents=True, exist_ok=True)
            CD(path)

        execute_download_command(url, filename, aria2_command, is_special_domain, is_google_drive, log, unzip)
    finally:
        CD(current_dir)

def handle_path_and_filename(parts):
    """Handle extraction of path and filename from parts."""
    if len(parts) >= 3:
        path = Path(parts[1]).expanduser()
        filename = parts[2]
    elif len(parts) >= 2:
        path = Path(parts[1]).expanduser() if '/' in parts[1] or '~/' in parts[1] else None
        filename = None if path else parts[1]
    else:
        path, filename = None, None

    return path, filename

def execute_download_command(url, filename, aria2_command, is_special_domain, is_google_drive, log, unzip):
    """Download a file from various sources (CivitAI, Google Drive, or general URLs) 
    using the appropriate method (aria2, gdown, or curl)."""
    if is_special_domain:
        command = f"{aria2_command} '{url}'"
        if not filename:
            filename = get_file_name(urlparse)
        if filename:
            command += f" -o '{filename}'"
        monitor_aria2_download(command, filename, url, log)
    elif is_google_drive:
        download_google_drive(url, filename, log)
    else:
        command = f"curl -#JL '{url}'"
        if filename:
            command += f" -o '{filename}'"
        run_command(command, filename, log)

    # Unpucking Zips
    if unzip and filename and filename.endswith('.zip'):
        unzip_file(filename, log)

def clean_url(url):
    """Clean and format URLs to ensure correct access."""
    if "civitai.com" in url:
        if '?token=' in url:
            url = url.split('?token=')[0]
        if '?type=' in url:
            url = url.replace('?type=', f'?token={cai_token}&type=')
        else:
            url = f"{url}?token={cai_token}"
        
        try:
            if "civitai.com/models/" in url:
                if '?modelVersionId=' in url:
                    version_id = url.split('?modelVersionId=')[1]
                    response = requests.get(f"https://civitai.com/api/v1/model-versions/{version_id}")
                else:
                    model_id = url.split('/models/')[1].split('/')[0]
                    response = requests.get(f"https://civitai.com/api/v1/models/{model_id}")

                data = response.json()

                if response.status_code != 200:
                      print(f"> \033[31m[CivitAI API Error]:\033[0m {response.status_code} - {response.text}")
                      return None

                early_access = data.get("earlyAccessEndsAt", None)
                if early_access:
                    model_id = data.get("modelId")
                    version_id = data.get("id")
                    
                    print(f"\n> \033[34m[CivitAI API]:\033[0m The model is in early access and requires payment for downloading.")
                    if model_id and version_id:
                        page = f"https://civitai.com/models/{model_id}?modelVersionId={version_id}"
                        print(f"> \033[32m[CivitAI Page]:\033[0m {page}\n")
                    return None

                download_url = data["downloadUrl"] if "downloadUrl" in data else data["modelVersions"][0]["downloadUrl"]
                return f"{download_url}?token={cai_token}"
        except Exception as e:
            print(f"> \033[31m[Error]:\033[0m  {e}")
            return None

    elif "huggingface.co" in url:
        if '/blob/' in url:
            url = url.replace('/blob/', '/resolve/')
        if '?' in url:
            url = url.split('?')[0]

    elif "github.com" in url:
        if '/blob/' in url:
            url = url.replace('/blob/', '/raw/')

    return url

def get_file_name(url):
    """Get the file name based on the URL."""
    if any(domain in url for domain in ["civitai.com", "drive.google.com"]):
        return None
    else:
        return Path(urlparse(url).path).name

def unzip_file(zip_filepath, log):
    """Extracts the ZIP file to the specified path."""
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(Path(zip_filepath).parent)  # Extract to the same directory
        if log:
            print(f"Successfully unpacked:  {zip_filepath}")
    except Exception as e:
        if log:
            print(f"An error occurred while unzipping {zip_filepath}: {e}")

def download_google_drive(url, filename=None, log=False):
    """Download a file or folder from Google Drive using gdown."""
    cmd = "gdown --fuzzy " + url
    if filename:
        cmd += " -O " + filename
    if "drive.google.com/drive/folders" in url:
        cmd += " --folder"

    execute_shell_command(cmd, log)


def monitor_aria2_download(command, filename, url, log):
    """Starts aria2c and intercepts the output to display the download progress."""
    try:
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        error_codes, error_messages = [], []
        result = ""
        br = False

        while True:
            lines = process.stderr.readline()
            if lines == '' and process.poll() is not None:
                break

            if lines:
                result += lines

                for output_line in lines.splitlines():
                    handle_error_output(lines, error_codes, error_messages)

                    if re.match(r'\[#\w{6}\s.*\]', output_line):
                        formatted_line = format_output_line(output_line)
                        if log:
                            for line in lines:
                                print(f"\r{' ' * 180}\r{formatted_line}", end="")
                                sys.stdout.flush()
                        br = True
                        break

        # Print collected error messages
        if log:
            for error in error_codes + error_messages:
                print(f" {error}")

            if br:
                print()

            # Print final status
            stripe = result.find("======+====+===========")
            if stripe != -1:
                for line in result[stripe:].splitlines():
                    if '|' in line and 'OK' in line:
                        formatted_line = re.sub(r'(\|\s*)(OK)(\s*\|)', r'\1\033[32m\2\033[0m\3', line)
                        print(f" {formatted_line}")

        process.wait()

    except KeyboardInterrupt:
        print("\n> Download interrupted")

def format_output_line(line):
    """Format a line of output with ANSI color codes."""
    line = re.sub(r'\[', "\033[35m【\033[0m", line)
    line = re.sub(r'\]', "\033[35m】\033[0m", line)
    line = re.sub(r'(#)(\w+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(\(\d+%\))', r'\033[36m\1\033[0m', line)
    line = re.sub(r'(CN:)(\d+)', r'\1\033[34m\2\033[0m', line)
    line = re.sub(r'(DL:)(\d+\w+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(ETA:)(\d+\w+)', r'\1\033[33m\2\033[0m', line)
    return line

def handle_error_output(line, error_codes, error_messages):
    """Check and collect error messages from the output."""
    if 'errorCode' in line or 'Exception' in line:
        error_codes.append(line)
    if '|' in line and 'ERR' in line:
        formatted_line = re.sub(r'(\|\s*)(ERR)(\s*\|)', r'\1\033[31m\2\033[0m\3', line)
        error_messages.append(formatted_line)


def run_command(command, filename, log):
    """Execute a shell command and handle logging."""
    execute_shell_command(command, log)

def execute_shell_command(command, log):
    try:
        process = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if log:
            for line in process.stderr:
                print(line, end="")
        process.wait()
    except KeyboardInterrupt:
        if log:
            print("\n> Canceled")

## ================ Clone ================
def m_clone(input_source, log=False):
    """Clone repositories from a given source."""
    input_path = Path(input_source).expanduser()

    def extract_repository_url(command):
        """Extract the repository URL from a git clone command."""
        command = command.strip()
        if command.startswith("git clone"):
            return command[len("git clone "):].strip()
        return command

    if input_source.endswith('.txt') and input_path.is_file():
        with open(input_path, 'r') as file:
            commands = [f"git clone {extract_repository_url(line)}" for line in file]
    else:
        commands = [f"git clone {extract_repository_url(input_source)}"] if isinstance(input_source, str) else [f"git clone {extract_repository_url(repo)}" for repo in input_source]

    execute_cloning(commands, log)

def execute_cloning(commands, log):
    """Execute the cloning commands."""
    for command in commands:
        command = command.strip()
        if not command:
            continue

        command_parts = shlex.split(command)
        repository_url = None

        for part in command_parts:
            if re.match(r'https?://', part):
                repository_url = part
                break

        # Clone the repository and only fetch the latest commit
        process = subprocess.Popen(
            command_parts + ['--depth', '1'],  # Add depth option to clone only the latest commit
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        while True:
            output_line = process.stdout.readline()
            if not output_line and process.poll() is not None:
                break

            if output_line:
                output_line = output_line.strip()
                if log:
                    if "fatal" in output_line:
                        print(f">>{'':>2}{output_line}")
                    elif output_line.startswith("Cloning into"):
                        repo_info = output_line.split("'")[1]
                        repo_name = "/".join(repo_info.split("/")[-3:])
                        print(f">>{'':>2}{repo_name} -> {repository_url}")

        process.wait()