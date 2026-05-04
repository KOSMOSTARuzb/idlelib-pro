import shutil
from pathlib import Path

def create_checkpoint(parent: Path) -> bool:
    """Saves the current state of the folder."""
    backup_folder = parent.parent / ".backup_k"
    if backup_folder.exists():
        print("Backup already exists. Overwriting...")
        remove_checkpoint(parent)
        return False

    shutil.copytree(parent, backup_folder)
    print("Backup created!")
    return True


def restore_checkpoint(parent: Path) -> bool:
    backup_folder = parent.parent / ".backup_k"
    """Resets the folder to the state of the last checkpoint."""
    if not backup_folder.exists():
        print("No backup found to restore.")
        return False

    # 1. Delete the modified folder
    if parent.exists():
        shutil.rmtree(parent)

    # 2. Restore from backup
    shutil.copytree(backup_folder, parent)
    print("Folder restored to original!")
    return True


def remove_checkpoint(parent: Path):
    backup_folder = parent.parent / ".backup_k"
    """Deletes the backup (if you are happy with the mod)."""
    if backup_folder.exists():
        shutil.rmtree(backup_folder)
        print("Backup removed.")
        return True
    return False

def check_checkpoint(parent: Path):
    backup_folder = parent.parent / ".backup_k"
    return backup_folder.exists()