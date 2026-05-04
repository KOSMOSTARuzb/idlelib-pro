import os
import zipfile
import winreg
import sys

from K_changes import injections
from K_utils import run_injections


def get_registry_subkeys(key_path):
    """Retrieves a list of subkeys within a specified registry key path."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            subkey_count = winreg.QueryInfoKey(key)[0]  # Number of subkeys
            subkeys = []
            for i in range(subkey_count):
                subkeys.append(winreg.EnumKey(key, i))

            return subkeys
    except FileNotFoundError:
        print(f"Registry key '{key_path}' not found.")
        return None

def get_reg_value(key_path:str, value_name:str):
    """Extracts value from the registry."""

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            executable_path, _ = winreg.QueryValueEx(key, value_name)
            return executable_path
    except FileNotFoundError:
        print("Registry key or value not found.")
        return None

def extract_zip(zip_path, destination_path):
    """Extracts zip to the directory."""
    
    print("From:",zip_path)
    print("To",destination_path)
    print("Extracting...")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(destination_path) 
    
    print("IDLElib extracted successfully!")

if __name__ == "__main__":
    key_path = r"Software\Python\PythonCore"
    print("Looking for python installation...")
    subkeys = get_registry_subkeys(key_path)

    if subkeys:
        subkeys.sort(reverse=True)
        print("Found",subkeys)
        for i in range(len(subkeys)):
            print('\n')
            try:
                key_path2=key_path + '\\' + subkeys[i]
                key_path2+='\\Idle'
                print("Getting value of",key_path2)

                idle_path = os.path.dirname(get_reg_value(key_path2, ''))
                print("Installing:",idle_path)
                run_injections(idle_path, injections)
            except Exception as e:
                print(e)

    else:
        print("No python installation found or an error occurred.")
os.system('pause')