import json
import os
import shutil
import platform
import subprocess
import dataclasses
from datetime import datetime
from tkinter import messagebox

BACKUP_DIR = "backup"
MAX_BACKUPS_PER_FILE = 3


def _create_backup(filepath):
    if not os.path.exists(filepath):
        return True
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        basename = os.path.basename(filepath)
        prefix = f"{basename.split('.')[0]}_"
        suffix = ".json"

        existing_backups = []
        for f in os.listdir(BACKUP_DIR):
            if f.startswith(prefix) and f.endswith(suffix):
                full_path = os.path.join(BACKUP_DIR, f)
                mtime = os.path.getmtime(full_path)
                existing_backups.append((full_path, mtime))

        existing_backups.sort(key=lambda x: x[1])

        while len(existing_backups) >= MAX_BACKUPS_PER_FILE:
            oldest_file_path, _ = existing_backups.pop(0)
            os.remove(oldest_file_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{prefix}{timestamp}{suffix}"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        shutil.copy2(filepath, backup_path)
        return True
    except Exception as e:
        messagebox.showerror(
            "Ошибка бэкапа",
            f"Не удалось создать резервную копию файла {filepath}!\n"
            f"Сохранение прервано для защиты данных.\n\nОшибка: {e}",
        )
        return False


def load_json(filepath, model=None):
    """Загружает JSON. Если передан model (dataclass), конвертирует данные в объекты."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if model and dataclasses.is_dataclass(model):
            # Превращаем список словарей в список объектов dataclass
            return [model(**item) for item in data]
        return data
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось прочитать {filepath}:\n{e}")
        return []


def save_json(filepath, data):
    if not _create_backup(filepath):
        return False

    try:
        # Автоматическая конвертация объектов dataclass обратно в словари для JSON
        if (
            data
            and isinstance(data, list)
            and len(data) > 0
            and dataclasses.is_dataclass(data[0])
        ):
            data = [dataclasses.asdict(item) for item in data]
        elif dataclasses.is_dataclass(data):
            data = dataclasses.asdict(data)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить {filepath}:\n{e}")
        return False


def open_pdf(filepath):
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.call(["open", filepath])
        else:
            subprocess.call(["xdg-open", filepath])
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть PDF:\n{e}")


def validate_and_create_dirs(dirs_to_check):
    missing = [d for d in dirs_to_check if d and not os.path.isdir(d)]
    if not missing:
        return True
    msg = (
        "⚠️ Не найдены следующие директории:\n"
        + "\n".join(missing)
        + "\n\nСоздать их автоматически?"
    )
    if messagebox.askyesno("Предупреждение", msg):
        for path in missing:
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку {path}:\n{e}")
                return False
        return True
    return False
