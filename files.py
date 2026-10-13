import os
from tinytag import TinyTag
import json
import random


def list_in_dir(name):
    try:
        return list(os.path.join(name, i) for i in os.listdir(name))
    except:
        return False


def filter_list(lst_in_dir, extensions=None):
    lst = []
    if extensions:
        for i in lst_in_dir:
            if check_file(i, extensions):
                lst.append(i)
        return lst
    return list(filter(os.path.isdir, lst_in_dir))
    

def check_directory(name_directory):
    try:
        os.mkdir(path=f'{name_directory}')
        return []
    except:
        return os.path.abspath(name_directory)
    
    
def create_dir(name_directory):
    os.makedirs(name_directory, exist_ok=True)


def check_file(name, extensions=('wav', 'flac', 'ogg', 'mat', 'aiff', 'au', 'caf', 'flac', 'htk',
                  'svx', 'voc', 'wve', 'raw', 'mpc', 'w64', 'aif', 'aifc', 'mp3')):
    if extensions:
        if os.path.isfile(name) and name.split('.')[-1] in extensions:
            return True
        return False
    return os.path.isdir(name)


def get_duration(name):
    if os.path.isdir(name):
        seconds = 0
        for i in list_in_dir(name):
            if check_file(i):
                seconds += TinyTag.get(i).duration
    else:        
        seconds = TinyTag.get(name).duration
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


def create_config(name, dct):
    try:
        with open(name, "w", encoding="utf-8") as file:
            json.dump(dct, file, indent=4, ensure_ascii=False)
        return True
    except:
        return False
        
        
def get_config(name):
    try:
        with open(f'{name}/config.json', "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except:
        return False
    
    
def random_sound(lst_sounds):
    if lst_sounds:
        name = random.choice(lst_sounds)
        return name
    
    
