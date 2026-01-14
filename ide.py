# Vcode
# Copyright (C) 2023-2026  Vladimir Varenik  <feedback.vcode@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/.


import sys
import json
from os import mkdir, listdir
from os.path import isfile, exists

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSettings

from functions import resource_path
from default import *

VERSION: str = '1.1.0'

style: dict[str, str] = {}
for file in listdir(resource_path('styles')):
    if isfile(resource_path('styles/' + file)) and file.endswith('.qss'):
        with open(resource_path('styles/' + file)) as qss:
            style[file[:-4]] = qss.read()

if exists(CONFIG_PATH + '/languages.json'):
    with open(CONFIG_PATH + '/languages.json') as llf:
        language_list: dict[str, dict[str, str]] = json.load(llf)
    if 'Python' not in language_list.keys():
        language_list["Python"] = python_ll
        with open(CONFIG_PATH + '/languages.json', 'w') as llf:
            json.dump(language_list, llf)
    if 'Html' not in language_list.keys():
        language_list["Html"] = html_ll
        with open(CONFIG_PATH + '/languages.json', 'w') as llf:
            json.dump(language_list, llf)
    if 'JSON' not in language_list.keys():
        language_list["JSON"] = json_ll
        with open(CONFIG_PATH + '/languages.json', 'w') as llf:
            json.dump(language_list, llf)
    if 'PHP' not in language_list.keys():
        language_list["PHP"] = php_ll
        with open(CONFIG_PATH + '/languages.json', 'w') as llf:
            json.dump(language_list, llf)
else:
    language_list: dict[str, dict[str, str]] = {"Python": python_ll, "Html": html_ll, "JSON": json_ll, "PHP": php_ll}
    if not exists(CONFIG_PATH):
        mkdir(CONFIG_PATH)
    with open(CONFIG_PATH + '/languages.json', 'w') as llf:
        json.dump(language_list, llf)
if not exists(CONFIG_PATH + '/extensions/'):
    mkdir(CONFIG_PATH + '/extensions/')
if not exists(CONFIG_PATH + '/highlights/'):
    mkdir(CONFIG_PATH + '/highlights/')
if not exists(CONFIG_PATH + '/highlights/python.hl'):
    with open(CONFIG_PATH + '/highlights/python.hl', 'w') as llf:
        llf.write(python_hl)
if not exists(CONFIG_PATH + '/highlights/html.hl'):
    with open(CONFIG_PATH + '/highlights/html.hl', 'w') as llf:
        llf.write(html_hl)
if not exists(CONFIG_PATH + '/highlights/json.hl'):
    with open(CONFIG_PATH + '/highlights/json.hl', 'w') as llf:
        llf.write(json_hl)
if not exists(CONFIG_PATH + '/highlights/php.hl'):
    with open(CONFIG_PATH + '/highlights/php.hl', 'w') as llf:
        llf.write(php_hl)


if __name__ == '__main__':
    from classes.idewindow import IdeWindow, HighlightMaker, ProjectSettingsDialog

    app: QApplication = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('Vcode.ico')))

    ide: IdeWindow = IdeWindow()

    if ide.settings.value('Recent') == 1:
        last: QSettings = QSettings('Vcode', 'Last')
        if last.value('project'):
            ide.open_project(last.value('project'))
        for n in last.allKeys():
            if n not in ('current', 'project') and last.value(n) is not None:
                ide.add_tab(n, int(last.value(n)))
            elif last.value('current') is not None:
                ide.editor_tabs.setCurrentIndex(int(last.value('current')))
        last.clear()

    for arg in sys.argv[1:]:
        pth: str = arg.replace('\\', '/').replace('"', '')
        if isfile(arg):
            if arg.endswith('.vcodeproject'):
                ide.open_project(pth[:-13])
                prs: ProjectSettingsDialog = ProjectSettingsDialog(ide.project, ide.project_path, ide)
                prs.exec()
            elif arg.endswith('.hl'):
                hm: HighlightMaker = HighlightMaker(pth)
                hm.setWindowTitle(f'{pth.rsplit('/', 1)[1]} - Vcode highlight maker')
                hm.exec()
            else:
                ide.add_tab(pth)

    ide.settings_window.autorun.setEnabled(False)
    ide.settings_window.autorun.setStyleSheet('font: italic;')

    sys.exit(app.exec())
