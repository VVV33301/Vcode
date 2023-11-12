STYLE = {
    'System': '',
    'Dark':
        '''
        QMainWindow {
            background-color: rgb(80, 80, 90);
        } 
        #empty {
            background-color: rgb(115, 115, 125);
            color: white;
        }
        QDialog, QWidget {
            background-color: rgb(80, 80, 90);
            color: white;
        }
        QMenuBar, QMenu, QToolBar {
            background-color: rgb(115, 115, 125);
            color: white;
        }
        QMenuBar::item:selected, QMenu:selected {
            background-color: rgb(105, 105, 115);
            color: rgb(245, 245, 245);
        }
        QTabBar {
            color: black;
        }
        QLabel, QRadioButton, QCheckBox {
            color: white;
        }
        QListView {
            color: white;
            border-radius: 6px;
            border-width: 2px;
            border-color: rgb(60, 60, 90);
            border-style: solid;
            height: 6em;
        }
        QTreeView::item:hover, QListView::item:hover {
            background-color: rgb(54, 54, 60);
        }
        QTreeView::item:selected, QListView::item:selected {
            background-color: rgb(45, 45, 54);
        }
        QGroupBox {
            padding-top: 18px;
            color: white;
            border-radius: 12px;
            border-width: 2px;
            border-color: rgb(60, 60, 90);
            border-style: solid;
            width: 6em;
        }
        QComboBox, QComboBox::drop-down {
            color: white;
            border-radius: 6px; 
            background-color: rgb(60, 60, 90);
        }
        QComboBox QAbstractItemView {
            background-color: rgb(90, 90, 120);
            color: white;
        }
        QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
            background-color: rgb(45, 45, 54);
        }
        QPushButton {
            color: white;
            border-radius: 6px;
            border-width: 2px;
            border-color: rgb(60, 60, 90);
            border-style: solid;
            background-color: rgb(65, 65, 75);
            height: 1.8em;
            width: 4.2em;
        }
        QAbstractButton:hover {
            background-color: rgb(90, 90, 100);
        }
        #exit_code {
            font-size: 18px;
        }
        ''',
    'Yellow':
        '''
        QMainWindow {
            background-color: rgb(245, 245, 215);
        }
        QDialog, QWidget {
            background-color: rgb(255, 255, 245);
        } 
        QMenuBar, QMenu, QToolBar {
            background-color: rgb(245, 245, 215);
        }
        QMenuBar::item:selected, QMenu:selected {
            background-color: rgb(215, 215, 195);
            color: rgb(245, 245, 245);
        }
        QTabBar {
            background-color: rgb(30, 30, 60);
            color: black;
        }
        QListView {
            border-radius: 6px;
            border-width: 2px;
            border-color: rgb(60, 60, 90);
            border-style: solid;
            height: 6em;
        }
        QTreeView::item:hover, QListView::item:hover {
            background-color: rgb(184, 184, 190);
        }
        QTreeView::item:selected, QListView::item:selected {
            background-color: rgb(175, 175, 184);
        }
        QGroupBox {
            padding-top: 18px;
            border-radius: 12px;
            border-width: 2px;
            border-color: rgb(60, 60, 90);
            border-style: solid;
            width: 6em;
        }
        QComboBox, QComboBox::drop-down {
            border-radius: 6px; 
            background-color: rgb(190, 190, 160);
        }
        QComboBox QAbstractItemView {
            background-color: rgb(220, 220, 190);
        }
        QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
            background-color: rgb(185, 185, 174);
        }
        #exit_code {
            font-size: 18px;
        }
        '''
}
