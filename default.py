from os.path import expanduser

USER: str = expanduser('~').replace('\\', '/')
CONFIG_PATH: str = f'{USER}/.Vcode'

ENCODINGS: list[str] = [
    'ascii', 'big5', 'big5hkscs', 'cp037', 'cp1006', 'cp1026', 'cp1125', 'cp1140', 'cp1250', 'cp1251', 'cp1252',
    'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258', 'cp273', 'cp424', 'cp437', 'cp500', 'cp720', 'cp737',
    'cp775', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864', 'cp865',
    'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'euc_jis_2004', 'euc_jisx0213', 'euc_jp', 'euc_kr',
    'gb18030', 'gb2312', 'gbk', 'hz', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_2004', 'iso2022_jp_3',
    'iso2022_jp_ext', 'iso2022_kr', 'iso8859-1', 'iso8859-10', 'iso8859-11', 'iso8859-13', 'iso8859-14', 'iso8859-15',
    'iso8859-16', 'iso8859-2', 'iso8859-3', 'iso8859-4', 'iso8859-5', 'iso8859-6', 'iso8859-7', 'iso8859-8',
    'iso8859-9', 'johab', 'koi8-r', 'koi8-t', 'koi8-u', 'kz1048', 'mac-cyrillic', 'mac-greek', 'mac-iceland',
    'mac-latin2', 'mac-roman', 'mac-turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004', 'shift_jisx0213', 'utf-16',
    'utf-16-be', 'utf-16-le', 'utf-32', 'utf-32-be', 'utf-32-le', 'utf-7', 'utf-8', 'utf-8-sig'
]

LANGUAGES: dict[str, str] = {'English': 'en', 'Русский': 'ru', 'Deutsch': 'de', '中国人': 'ch', 'हिंदी': 'hi'}

python_hl: str = r'''class|def|for|while|if|elif|else|try|except|finally|with|match|case = {"tab": 1};
self|class|def|for|while|if|elif|else|try|except|finally|with|import|from|match|case|lambda|as|in|is|not|and|or|True|False|None|async|await|del|return|raise|yield|pass|assert|__build_class__|__debug__|__doc__|__import__|__loader__|__name__|__package__|__spec__|abs|aiter|all|anext|any|ascii|bin|bool|breakpoint|bytearray|bytes|callable|chr|classmethod|compile|complex|copyright|credits|delattr|dict|dir|divmod|enumerate|eval|exec|exit|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|license|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|property|quit|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip|ArithmeticError|AssertionError|AttributeError|BaseException|BaseExceptionGroup|BlockingIOError|BrokenPipeError|BufferError|BytesWarning|ChildProcessError|ConnectionAbortedError|ConnectionError|ConnectionRefusedError|ConnectionResetError|DeprecationWarning|EOFError|Ellipsis|EncodingWarning|EnvironmentError|Exception|ExceptionGroup|FileExistsError|FileNotFoundError|FloatingPointError|FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|IndentationError|IndexError|InterruptedError|IsADirectoryError|KeyError|KeyboardInterrupt|LookupError|MemoryError|ModuleNotFoundError|NameError|NotADirectoryError|NotImplemented|NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|PermissionError|ProcessLookupError|RecursionError|ReferenceError|ResourceWarning|RuntimeError|RuntimeWarning|StopAsyncIteration|StopIteration|SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|TimeoutError|TypeError|UnboundLocalError|UnicodeDecodeError|UnicodeEncodeError|UnicodeError|UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|Warning|WindowsError|ZeroDivisionError = {"complete": 1};
\b(def|class) \w+\b = {"foreground": [80, 160, 255]};
\b__\w+__\b = {"foreground": [255, 0, 255]};
\b(ArithmeticError|AssertionError|AttributeError|BaseException|BaseExceptionGroup|BlockingIOError|BrokenPipeError|BufferError|BytesWarning|ChildProcessError|ConnectionAbortedError|ConnectionError|ConnectionRefusedError|ConnectionResetError|DeprecationWarning|EOFError|Ellipsis|EncodingWarning|EnvironmentError|Exception|ExceptionGroup|FileExistsError|FileNotFoundError|FloatingPointError|FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|IndentationError|IndexError|InterruptedError|IsADirectoryError|KeyError|KeyboardInterrupt|LookupError|MemoryError|ModuleNotFoundError|NameError|NotADirectoryError|NotImplemented|NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|PermissionError|ProcessLookupError|RecursionError|ReferenceError|ResourceWarning|RuntimeError|RuntimeWarning|StopAsyncIteration|StopIteration|SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|TimeoutError|TypeError|UnboundLocalError|UnicodeDecodeError|UnicodeEncodeError|UnicodeError|UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|Warning|WindowsError|ZeroDivisionError|__build_class__|__debug__|__doc__|__import__|__loader__|__name__|__package__|__spec__|abs|aiter|all|anext|any|ascii|bin|bool|breakpoint|bytearray|bytes|callable|chr|classmethod|compile|complex|copyright|credits|delattr|dict|dir|divmod|enumerate|eval|exec|exit|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|license|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|property|quit|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip)\b = {"foreground": [136, 136, 198]};
^\s*@([\w.]+) = {"foreground": [127, 255, 127]};
\b(class|def|for|while|if|elif|else|try|except|finally|with|import|from|match|case|lambda|as|in|is|not|and|or|True|False|None|async|await|del|return|raise|yield|pass|assert)\b = {"foreground": [255, 127, 0]};
\bself\b = {"foreground": [195, 15, 195]};
\b\d+(\.\d+)? = {"foreground": [30, 180, 210]};
0b[0-1]+|0o[0-7]+|0x[0-9a-fA-F]+ = {"foreground": [20, 170, 180]};
(#[^\n]*) = {"foreground": [127, 127, 127]};
(r|f|b|c|u|)("([^"]*)"|'([^']*)') = {"foreground": [0, 240, 0]};'''
html_hl: str = r'''a|abbr|above|absolute|accept|accesskey|action|address|alt|always|aqua|area|armenian|article|aside|async|attr|audio|auto|autocomplete|autofocus|autoplay|avoid|azimuth|b|background|base|baseline|bdi|bdo|behind|below|bgsound|black|blink|block|blockquote|blue|body|bold|bolder|border|both|bottom|br|button|canvas|capitalize|caption|cellpadding|cellspacing|center|challenge|charset|checked|circle|cite|class|clear|clip|code|col|colgroup|collapse|color|cols|colspan|command|compact|condensed|content|contenteditable|contextmenu|continuous|controls|coords|crop|cros|crosshair|cue|cursor|data|datalist|datetime|dd|decimal|default|defer|deg|del|details|dfn|dialog|digits|dir|direction|disabled|disc|display|div|dl|draggable|dropzone|dt|element|elevation|em|embed|enctype|ex|expanded|fast|faster|fieldset|figcaption|figure|fixed|float|font|footer|for|form|formaction|formenctype|formmethod|formnovalidate|formtarget|frame|frameset|fuchsia|georgian|grad|gray|green|h1|h2|h3|h4|h5|h6|head|header|headers|hebrew|height|help|hgroup|hidden|hide|high|higher|hiragana|hr|href|hreflang|html|hz|i|icon|id|iframe|img|inherit|inline|input|ins|inside|ismap|italic|justify|katakana|kbd|keygen|keytype|khz|kind|label|landscape|lang|left|leftwards|legend|level|li|lighter|lime|link|list|loop|loud|low|lower|lowercase|ltr|manifest|map|margin|mark|marker|marks|maroon|marquee|max|maxlength|media|medium|menu|menuitem|meta|meter|method|middle|min|minlength|mix|move|ms|multicol|multiple|muted|name|narrower|nav|navy|nobr|noframes|none|normal|noscript|novalidate|nowrap|object|oblique|ol|olive|onabort|onautocomplete|onautocompleteerror|onbeforeprint|onbeforeunload|onblur|oncancel|oncanplay|oncanplaythrough|once|onchange|onclick|onclose|oncontextmenu|oncuechange|ondblclick|ondrag|ondragend|ondragenter|ondragexit|ondragleave|ondragover|ondragstart|ondrop|ondurationchange|onemptied|onended|onerror|onfocus|onhashchange|oninput|oninvalid|onkeydown|onkeypress|onkeyup|onload|onloadeddata|onloadedmetadata|onloadstart|onmessage|onmousedown|onmouseenter|onmouseleave|onmousemove|onmouseout|onmouseover|onmouseup|onmousewheel|onoffline|ononline|onpagehide|onpageshow|onpause|onplay|onplaying|onpointercancel|onpointerdown|onpointerenter|onpointerleave|onpointerlockchange|onpointerlockerror|onpointermove|onpointerout|onpointerover|onpointerup|onpopstate|onprogress|onratechange|onreadystatechange|onredo|onreset|onresize|onscroll|onseeked|onseeking|onselect|onshow|onsort|onstalled|onstorage|onsubmit|onsuspend|ontimeupdate|ontoggle|onundo|onunload|onvolumechange|onwaiting|open|optgroup|optimum|option|orphans|outline|output|outside|overflow|overline|p|padding|page|param|pattern|pause|picture|pitch|placeholder|pointer|portrait|position|poster|pre|preload|progress|pt|pubdate|purple|px|q|quotes|rad|radiogroup|readonly|red|rel|relative|repeat|required|reversed|richness|right|rightwards|rows|rowspan|rp|rt|rtc|rtl|ruby|s|samp|sandbox|scope|scoped|script|scroll|seamless|section|select|selected|separate|shadow|shape|show|silent|silver|size|sizes|slow|slower|small|soft|source|span|speak|spellcheck|square|src|srcdoc|srclang|start|static|step|stress|strike|strong|style|sub|summary|sup|super|svg|tabindex|table|target|tbody|td|teal|template|text|textarea|tfoot|th|thead|time|title|titleonafterprint|top|tr|track|transparent|type|u|ul|underline|uppercase|usemap|value|var|video|visibility|visible|volume|wait|wbr|white|wider|widows|width|wrap|xmlns|yellow = {"complete": 1};
\<(|/)\w[^\>]*\> = {"foreground": [240, 240, 0]};
"([^"]*)"|'([^']*)' = {"foreground": [0, 240, 0]};'''
json_hl: str = r'''\b\d+(\.\d+)? = {"foreground": [30, 180, 210]};
\b(true|false|null)\b = {"foreground": [255, 127, 0]};
"([^"\\]*(?:\\.[^"\\]*)*)" = {"foreground": [0, 240, 0]};
"([^"]*)"(?!:)*(?=:) = {"foreground": [240, 0, 240]};'''
php_hl: str = r'''\$\w+ = {"foreground": [240, 127, 0]};
\b\d+(\.\d+)? = {"foreground": [30, 180, 210]};
a|abbr|above|absolute|accept|accesskey|action|address|alt|always|aqua|area|armenian|article|aside|async|attr|audio|auto|autocomplete|autofocus|autoplay|avoid|azimuth|b|background|base|baseline|bdi|bdo|behind|below|bgsound|black|blink|block|blockquote|blue|body|bold|bolder|border|both|bottom|br|button|canvas|capitalize|caption|cellpadding|cellspacing|center|challenge|charset|checked|circle|cite|class|clear|clip|code|col|colgroup|collapse|color|cols|colspan|command|compact|condensed|content|contenteditable|contextmenu|continuous|controls|coords|crop|cros|crosshair|cue|cursor|data|datalist|datetime|dd|decimal|default|defer|deg|del|details|dfn|dialog|digits|dir|direction|disabled|disc|display|div|dl|draggable|dropzone|dt|element|elevation|em|embed|enctype|ex|expanded|fast|faster|fieldset|figcaption|figure|fixed|float|font|footer|for|form|formaction|formenctype|formmethod|formnovalidate|formtarget|frame|frameset|fuchsia|georgian|grad|gray|green|h1|h2|h3|h4|h5|h6|head|header|headers|hebrew|height|help|hgroup|hidden|hide|high|higher|hiragana|hr|href|hreflang|html|hz|i|icon|id|iframe|img|inherit|inline|input|ins|inside|ismap|italic|justify|katakana|kbd|keygen|keytype|khz|kind|label|landscape|lang|left|leftwards|legend|level|li|lighter|lime|link|list|loop|loud|low|lower|lowercase|ltr|manifest|map|margin|mark|marker|marks|maroon|marquee|max|maxlength|media|medium|menu|menuitem|meta|meter|method|middle|min|minlength|mix|move|ms|multicol|multiple|muted|name|narrower|nav|navy|nobr|noframes|none|normal|noscript|novalidate|nowrap|object|oblique|ol|olive|onabort|onautocomplete|onautocompleteerror|onbeforeprint|onbeforeunload|onblur|oncancel|oncanplay|oncanplaythrough|once|onchange|onclick|onclose|oncontextmenu|oncuechange|ondblclick|ondrag|ondragend|ondragenter|ondragexit|ondragleave|ondragover|ondragstart|ondrop|ondurationchange|onemptied|onended|onerror|onfocus|onhashchange|oninput|oninvalid|onkeydown|onkeypress|onkeyup|onload|onloadeddata|onloadedmetadata|onloadstart|onmessage|onmousedown|onmouseenter|onmouseleave|onmousemove|onmouseout|onmouseover|onmouseup|onmousewheel|onoffline|ononline|onpagehide|onpageshow|onpause|onplay|onplaying|onpointercancel|onpointerdown|onpointerenter|onpointerleave|onpointerlockchange|onpointerlockerror|onpointermove|onpointerout|onpointerover|onpointerup|onpopstate|onprogress|onratechange|onreadystatechange|onredo|onreset|onresize|onscroll|onseeked|onseeking|onselect|onshow|onsort|onstalled|onstorage|onsubmit|onsuspend|ontimeupdate|ontoggle|onundo|onunload|onvolumechange|onwaiting|open|optgroup|optimum|option|orphans|outline|output|outside|overflow|overline|p|padding|page|param|pattern|pause|picture|pitch|placeholder|pointer|portrait|position|poster|pre|preload|progress|pt|pubdate|purple|px|q|quotes|rad|radiogroup|readonly|red|rel|relative|repeat|required|reversed|richness|right|rightwards|rows|rowspan|rp|rt|rtc|rtl|ruby|s|samp|sandbox|scope|scoped|script|scroll|seamless|section|select|selected|separate|shadow|shape|show|silent|silver|size|sizes|slow|slower|small|soft|source|span|speak|spellcheck|square|src|srcdoc|srclang|start|static|step|stress|strike|strong|style|sub|summary|sup|super|svg|tabindex|table|target|tbody|td|teal|template|text|textarea|tfoot|th|thead|time|title|titleonafterprint|top|tr|track|transparent|type|u|ul|underline|uppercase|usemap|value|var|video|visibility|visible|volume|wait|wbr|white|wider|widows|width|wrap|xmlns|yellow = {"complete": 1};
\<(|/)\w[^\>]*\> = {"foreground": [240, 240, 0]};
\<\?php|\<\?\=|\?\> = {"foreground": [240, 0, 0]};
"([^"]*)"|'([^']*)' = {"foreground": [0, 240, 0]};'''

python_ll: dict[str, str] = {
    "highlight": f"{CONFIG_PATH}/highlights/python.hl",
    "file_formats": ["py", "pyw", "pyi"],
    "start_command": "python \"{filename}\"",
    "debug_command": "python -m pdb \"{filename}\""
}
html_ll: dict[str, str] = {
    "highlight": f"{CONFIG_PATH}/highlights/html.hl",
    "file_formats": ["htm", "html"],
    "start_command": "start \"\" \"{filename}\"",
    "debug_command": ""
}
json_ll: dict[str, str] = {
    "highlight": f"{CONFIG_PATH}/highlights/json.hl",
    "file_formats": ["json"],
    "start_command": "",
    "debug_command": ""
}
php_ll: dict[str, str] = {
    "highlight": f"{CONFIG_PATH}/highlights/php.hl",
    "file_formats": ["php"],
    "start_command": "php \"{filename}\"",
    "debug_command": ""
}
