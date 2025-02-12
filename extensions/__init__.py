import sys
from os import listdir, mkdir
from os.path import exists, abspath, dirname
from default import USER

mains = {}
for py in [f[:-3] for f in listdir(dirname(abspath(__file__))) if f.endswith('.py') and f != '__init__.py']:
    mod = __import__(__name__ + '.' + py, fromlist=[py])
    mains[py] = getattr(mod, 'main')
if not exists(USER + '/.Vcode/extensions'):
    mkdir(USER + '/.Vcode/extensions/')
sys.path.append(USER + '/.Vcode/extensions/')
for py in [f[:-3] for f in listdir(USER + '/.Vcode/extensions') if f.endswith('.py') and f != '__init__.py']:
    try:
        mod = __import__(py, fromlist=[py])
        mains[py] = getattr(mod, 'main')
    except AttributeError or ImportError:
        pass
