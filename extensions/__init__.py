import sys
from os import listdir, mkdir
from os.path import exists, abspath, dirname
from default import CONFIG_PATH

mains: dict[str, getattr] = {}
for py in [f[:-3] for f in listdir(dirname(abspath(__file__))) if f.endswith('.py') and f != '__init__.py']:
    try:
        mod = __import__(__name__ + '.' + py, fromlist=[py])
        mains[py] = getattr(mod, 'main')
    except ImportError:
        pass
if not exists(CONFIG_PATH + '/extensions'):
    mkdir(CONFIG_PATH + '/extensions/')
sys.path.append(CONFIG_PATH + '/extensions/')
for py in [f[:-3] for f in listdir(CONFIG_PATH + '/extensions') if f.endswith('.py') and f != '__init__.py']:
    try:
        mod = __import__(py, fromlist=[py])
        mains[py] = getattr(mod, 'main')
    except AttributeError or ImportError:
        pass
