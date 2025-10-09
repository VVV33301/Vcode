from os.path import join, dirname, abspath
import sys


def resource_path(relative_path: str) -> str:
    """Return absolute path of file"""
    return join(getattr(sys, '_MEIPASS', dirname(abspath(sys.argv[0]))), relative_path)


def set_autorun(enabled: bool) -> None:
    """Set program autorun on start operating system (only for Windows)"""
    if sys.platform == 'win32':
        from winreg import HKEYType, HKEY_CURRENT_USER, KEY_ALL_ACCESS, REG_SZ, OpenKey, SetValueEx, DeleteValue
        key: HKEYType = OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                                0, KEY_ALL_ACCESS)
        if enabled:
            SetValueEx(key, 'Vcode', 0, REG_SZ, sys.argv[0])
        else:
            DeleteValue(key, 'Vcode')
        key.Close()


def update_filters(lang: dict[str, dict[str, str]]) -> list[str]:
    """Add filters for file searching"""
    filters_f: list = ['All Files (*.*)']
    for i, j in lang.items():
        filters_f.append(f'{i} Files (*.{" *.".join(j["file_formats"])})')
    return filters_f
