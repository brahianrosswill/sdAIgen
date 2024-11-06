import json
import os

def read_json(filepath, key, default=None):
    """Reads a value by key from a JSON file, supporting nested structures."""
    if not os.path.exists(filepath):
        return default

    with open(filepath, 'r') as json_file:
        data = json.load(json_file)

    keys = key.split('.')
    current_level = data

    for part in keys:
        if part in current_level:
            current_level = current_level[part]
        else:
            return default  # Return default if key not found

    return current_level

def save_json(filepath, key, value):
    """Saves a value by key in a JSON file, supporting nested structures."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}

    keys = key.split('.')
    current_level = data

    for part in keys[:-1]:  # Traverse all keys except the last
        if part not in current_level:
            current_level[part] = {}  # Create nested dictionary if it doesn't exist
        current_level = current_level[part]

    current_level[keys[-1]] = value  # Save value by the last key

    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def update_json(filepath, key, value):
    """Updates a value by key in a JSON file, supporting nested structures, 
    appending if the key already exists."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}

    keys = key.split('.')
    current_level = data

    for part in keys[:-1]:  # Traverse all keys except the last
        if part not in current_level:
            current_level[part] = {}  # Create nested dictionary if it doesn't exist
        current_level = current_level[part]

    last_key = keys[-1]
    
    # If the last key already exists and is a dictionary, merge the new value
    if last_key in current_level and isinstance(current_level[last_key], dict):
        current_level[last_key].update(value)  # Merge dictionaries
    else:
        current_level[last_key] = value  # Save value by the last key

    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def key_or_value_exists(filepath, key=None, value=None):
    """Checks for the existence of a key or value in a JSON file, supporting nested structures."""
    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r') as json_file:
        data = json.load(json_file)

    keys = key.split('.') if key else []
    current_level = data

    for part in keys:
        if part in current_level:
            current_level = current_level[part]
        else:
            return None  # Return None if key not found

    if value is not None:
        # Check for value existence
        if current_level == value:
            return True
        else:
            return None
    else:
        # If value is not specified, just check for key existence
        return True

def delete_key(filepath, key):
    """Deletes a key from a JSON file, supporting nested structures."""
    if not os.path.exists(filepath):
        return  # Do nothing if file does not exist

    with open(filepath, 'r') as json_file:
        data = json.load(json_file)

    keys = key.split('.')
    current_level = data

    for part in keys[:-1]:  # Traverse all keys except the last
        if part in current_level:
            current_level = current_level[part]
        else:
            return  # Do nothing if key not found

    # Delete the last key if it exists
    last_key = keys[-1]
    if last_key in current_level:
        del current_level[last_key]

    # Save modified data back to file
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)