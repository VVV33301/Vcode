from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QTextDocument, QColor
import json
import re


class Highlighter(QSyntaxHighlighter):
    """Highlighter for code"""

    def __init__(self, highlight_path: str, parent: QTextDocument | None = None) -> None:
        super().__init__(parent)
        self.path: str = highlight_path
        self.mapping: dict[str, QTextCharFormat] = {}
        self.tab_words: list[str] = []
        self.complete_words: list[str] = []
        with open(highlight_path) as highlight_file:
            for string in highlight_file.read().replace('\n', '').split(';')[:-1]:
                expression, parameters = string.rsplit(' = ', maxsplit=1)
                params: dict[str, str] = json.loads(parameters)
                text_char: QTextCharFormat = QTextCharFormat()
                for parameter in params.keys():
                    match parameter:
                        case 'foreground':
                            text_char.setForeground(QColor(*params['foreground']))
                        case 'background':
                            text_char.setBackground(QColor(*params['background']))
                        case 'weight':
                            text_char.setFontWeight(int(params['weight']))
                        case 'italic':
                            text_char.setFontItalic(bool(params['italic']))
                        case 'underline':
                            text_char.setFontUnderline(bool(params['underline']))
                        case 'underline_color':
                            text_char.setUnderlineColor(QColor(*params['underline_color']))
                        case 'underline_style':
                            text_char.setUnderlineStyle(QTextCharFormat.UnderlineStyle(int(params['underline_style'])))
                        case 'tab':
                            if params['tab'] == 1:
                                for i in expression.split('|'):
                                    self.tab_words.append(i)
                        case 'complete':
                            if params['complete'] == 1:
                                for i in expression.split('|'):
                                    self.complete_words.append(i)
                self.mapping[rf'{expression}']: QTextCharFormat = text_char

    def highlightBlock(self, text: str) -> None:
        """Highlight the block of text"""
        for pattern, char in self.mapping.items():
            for match in re.finditer(pattern, text, re.MULTILINE):
                s, e = match.span()
                self.setFormat(s, e - s, char)
