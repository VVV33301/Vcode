from os.path import join, dirname, abspath, exists
import sys

from default import CONFIG_PATH


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


def load_history(*, new_item: str | None = None, return_list: bool = False, clear: bool = False) -> list[str] | None:
    """Return last 10 links from history"""
    if not exists(CONFIG_PATH + '\\history.txt') or clear:
        open(CONFIG_PATH + '/history.txt', 'w', encoding='utf-8').close()
    if new_item:
        with open(CONFIG_PATH + '\\history.txt', 'a', encoding='utf-8') as hf:
            hf.write(new_item + '\n')
    if return_list:
        with open(CONFIG_PATH + '\\history.txt', encoding='utf-8') as hf:
            ret: list[str] = []
            for line in hf.read().strip().splitlines()[::-1]:
                if line not in ret:
                    ret.append(line)
                    if len(ret) == 10:
                        return ret
            return ret
