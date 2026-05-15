import os
os.system('')
import zipfile
import winreg
import sys
import msvcrt
from pathlib import Path

from K_changes import injections
from K_utils import run_injections, check_status, get_current_path
from checkpoint import check_checkpoint, restore_checkpoint, create_checkpoint


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


def render_menu(title, subtitle, options, current_selection):
    os.system('cls')
    print(f"=== {title} ===")
    if subtitle:
        print(subtitle)
    print("-" * 50)
    for i, label in enumerate(options):
        if i == current_selection:
            if label in ("Exit", "Go Back", "Uninstall / Restore Original"):
                print(f"> \033[91m{label}\033[0m")  # Red
            else:
                print(f"> \033[92m{label}\033[0m")  # Green
        else:
            print(f"  {label}")
    print("-" * 50)


def main(idle_paths):
    if not idle_paths:
        print("No paths found to select.")
        return

    version_options = [f"Python {v}" for v in idle_paths.keys()] + ["Run the Server", "Exit"]
    v_selection = 0

    while True:
        # 1. Version Selection Menu
        while True:
            render_menu("IDLElib-Pro Installer", "Select the IDLE version to modify:", version_options, v_selection)
            key = msvcrt.getch()
            if key in (b'\x00', b'\xe0'):
                key = msvcrt.getch()
                if key == b'H':
                    v_selection = (v_selection - 1) % len(version_options)
                elif key == b'P':
                    v_selection = (v_selection + 1) % len(version_options)
            elif key in (b'\r', b'\n'):
                break

        selected_label = version_options[v_selection]
        if selected_label == "Exit":
            os.system('cls')
            print("Installation cancelled.")
            return
        
        elif selected_label == "Run the Server":
            os.system('cls')
            print("Launching the Server...")

            server_dir = os.path.join(get_current_path(), "K_change_assets")
            server_path = os.path.join(server_dir, "k_server.py")

            if server_dir not in sys.path:
                sys.path.insert(0, server_dir)

            try:
                with open(server_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    # This turns the current process into the server
                    exec(code, {'__name__': '__main__', '__file__': server_path})
                    print("Closed the Server...")
            except Exception as e:
                print(f"Failed to launch server: {e}")

            return

        version_key = selected_label.replace("Python ", "")
        selected_path = idle_paths[version_key]
        path_obj = Path(selected_path)
        a_selection = 0

        while True:
            # 2. Action Menu for Selected Version
            status, error_message = check_status(selected_path)

            subtitle = f"Target: {selected_label}\nPath: {selected_path}\nStatus: {status}"
            if error_message:
                subtitle+="\n\n"+error_message
                actions = ["Go Back"]
            elif status != '[INSTALLED]':
                actions = ["Install Patches", "Go Back"]
            else:
                actions = ["Repair and Reinstall", "Uninstall / Restore Original", "Go Back"]

            a_selection = a_selection % len(actions)
            render_menu(selected_label, subtitle, actions, a_selection)

            key = msvcrt.getch()
            if key in (b'\x00', b'\xe0'):
                key = msvcrt.getch()
                if key == b'H':
                    a_selection = (a_selection - 1) % len(actions)
                elif key == b'P':
                    a_selection = (a_selection + 1) % len(actions)
            elif key in (b'\r', b'\n'):
                action = actions[a_selection]
                if action == "Go Back":
                    break

                os.system('cls')
                print(f"Executing: {action}...")
                print("-" * 50)
                try:
                    if action == "Install Patches":
                        create_checkpoint(Path(selected_path))
                        run_injections(selected_path, injections)

                    elif action == "Repair and Reinstall":
                        if restore_checkpoint(Path(selected_path)):
                            print("Restored to original...")
                            print("Proceeding with the installation...")
                            run_injections(selected_path, injections)
                    elif action == "Uninstall / Restore Original":
                        if restore_checkpoint(path_obj):
                            print("Successfully restored original files.")
                        else:
                            print("Restore failed.")
                    else:
                        print("Critical error")
                except Exception as e:
                    print(f"Error: {e}")

                print("-" * 50)
                print("Press any key to return...")
                msvcrt.getch()

if __name__ == "__main__":
    key_path = r"Software\Python\PythonCore"
    print("Looking for python installation...")
    subkeys = get_registry_subkeys(key_path)

    if subkeys:
        subkeys.sort(reverse=True)
        print("Found",subkeys)
        idle_paths = {}
        for i in range(len(subkeys)):
            print('\n')
            try:
                key_path2=key_path + '\\' + subkeys[i]
                key_path2+='\\Idle'
                print("Getting value of",key_path2)

                idle_path = os.path.dirname(get_reg_value(key_path2, ''))
                idle_paths[subkeys[i]] = idle_path
            except Exception as e:
                print(e)
        main(idle_paths)

    else:
        print("No python installation found or an error occurred.")
os.system('pause')