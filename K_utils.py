import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

from K_types import Injection, SearchType, ChangeType
from checkpoint import check_checkpoint, restore_checkpoint, create_checkpoint


def run_injection(source_path:str, destination_path: str, injection: Injection) -> None:
    destination_file_path = os.path.join(destination_path, injection.search.file_path)
    indexes = []
    if os.path.isfile(destination_file_path):
        with open(destination_file_path, "r") as f:
            file_contents = f.read()
    if injection.search.search_type == SearchType.TEXT:
        assert not injection.search.search_query is None
        while True:
            current_index = file_contents.find(injection.search.search_query) if len(indexes)==0 else file_contents.find(injection.search.search_query, indexes[-1]+1)
            if current_index == -1 or (not injection.change.limit is None and len(indexes)>=injection.change.limit):
                break
            indexes.append(current_index + len(injection.search.search_query))
    elif injection.search.search_type == SearchType.BEGINNING:
        indexes = [0]
    elif injection.search.search_type == SearchType.ANY:
        pass
    else:
        assert False # Not implemented
    indexes.sort(reverse=True)

    if injection.change.change_type == ChangeType.OVERWRITE:
        if injection.change.change_query:
            with open(destination_file_path, "w") as f:
                f.write(injection.change.change_query)
        else:
            assert not injection.change.change_file_path is None
            source_file_path = os.path.join(source_path, injection.change.change_file_path)
            if os.path.isdir(source_file_path):
                shutil.copytree(source_file_path, destination_file_path)
            else:
                assert os.path.isfile(source_file_path)
                shutil.copy(source_file_path, destination_file_path)
        return

    def get_line_index(current_ix: int, file_length: int):
        if injection.search.search_type == SearchType.BEGINNING:
            return 0
        if injection.change.change_type == ChangeType.ADD_NEXT_LINE:
            while current_ix < file_length:
                current_ix += 1
                if file_contents[current_ix - 1] == '\n':
                    return current_ix
            return file_length
        elif injection.change.change_type == ChangeType.ADD_BEFORE_LINE:
            while current_ix > 0:
                current_ix -= 1
                if file_contents[current_ix] == '\n':
                    return current_ix + 1
            return 0
        else:
            assert False, "Unimplemented"

    for index in indexes:
        target_index = get_line_index(index, len(file_contents))
        injection_text = ''
        if injection.change.change_query:
            injection_text = injection.change.change_query
        else:
            assert not injection.change.change_file_path is None
            with open(os.path.join(source_path, injection.change.change_file_path), "r") as f:
                injection_text = f.read()
        file_contents = file_contents[:target_index] + injection_text + '\n' + file_contents[target_index:]

    with open(destination_file_path, "w") as f:
        f.write(file_contents)


def run_injections(destination_path: str, injections: List[Injection]) -> None:
    # if os.path.exists(os.path.join(destination_path, 'kosmostar.py')):
    #     print("This app was already installed last year. Please choose `Repair` option in the Python installer.\nSkipping installation...")
    #     return
    # if os.path.exists(os.path.join(destination_path, 'modded')):
    #     print("This app is already installed.")
    #     if not check_checkpoint(Path(destination_path)):
    #         print("There seems to be no backups of original IDLE.")
    #         print("Skipping installation...")
    #         return
    #     while True:
    #         prompt_answer = input("Do you want to repair the IDLE and reinstall? Enter r to restore only. (Y/n/r): ")
    #         if prompt_answer.lower() == 'y' or prompt_answer.lower() == 'yes' or prompt_answer.strip() == '':
    #             break
    #         elif prompt_answer.lower() == 'n' or prompt_answer.lower() == 'no':
    #             print("Skipping installation...")
    #             return
    #         elif prompt_answer.lower() == 'r':
    #             restore_checkpoint(Path(destination_path))
    #             print("Skipping installation...")
    #             return
    #         else:
    #             print("Try again...")
    #     if restore_checkpoint(Path(destination_path)):
    #         print("Proceeding with the installation...")
    #     else:
    #         return
    # elif os.path.exists(os.path.join(destination_path, 'mod_started')):
    #     print("This app is partially installed or corrupted.\nSkipping installation...")
    #     return
    # else:
    #     create_checkpoint(Path(destination_path))
    #


    Path(os.path.join(destination_path, 'mod_started')).touch(exist_ok=False)
    for injection in injections:
        print(injection)
        run_injection(get_current_path(), destination_path, injection)
        print("Done")
    Path(os.path.join(destination_path, 'modded')).touch()


def check_status(destination_path: str) -> Tuple[str, str | None]:
    path_obj = Path(destination_path)
    has_backups = check_checkpoint(path_obj)
    is_ancient_version = os.path.exists(os.path.join(destination_path, 'kosmostar.py'))
    is_modded = os.path.exists(os.path.join(destination_path, 'modded'))
    is_mod_started = os.path.exists(os.path.join(destination_path, 'mod_started'))

    error_message = None

    status = "[ORIGINAL]"
    if is_ancient_version:
        status = "[OUTDATED_VERSION]"
        error_message = "This app was already installed last year. Please choose `Repair` option in the Python installer.\nSkipping installation..."
    elif is_modded:
        if has_backups:
            status = "[INSTALLED]"
        else:
            status = "[INSTALLED_WITHOUT_BACKUP]"
            error_message = "There seems to be no backups of original IDLE."
    elif is_mod_started:
        status = "[UNFINISHED_INSTALLATION]"
        error_message = "This app is partially installed or corrupted.\nSkipping installation..."

    return status, error_message

def get_current_path()->str:
    data_dir: str
    if getattr(sys, 'frozen', False):  # Check if running as a frozen executable
        data_dir = sys._MEIPASS
    else:
        data_dir = os.path.dirname(__file__)  # Use current directory when running normally
    return data_dir