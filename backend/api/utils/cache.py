import os
import json
import time

CACHE_DIR = 'api/services/cache'


def get_cache(file_name, max_age_seconds):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    try:
        file_path = os.path.join(CACHE_DIR, file_name)
        if not os.path.exists(file_path):
            return None

        file_stat = os.stat(file_path)
        file_age = time.time() - file_stat.st_mtime
        if file_age > max_age_seconds:
            return None

        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Error reading cache file {file_name}: {e}")
        return None


def set_cache(file_name, data):
    try:
        file_path = os.path.join(CACHE_DIR, file_name)
        with open(file_path, 'w') as file:
            json.dump(data, file, default=str)
    except Exception as e:
        print(f"Error writing to cache file {file_name}: {e}")
