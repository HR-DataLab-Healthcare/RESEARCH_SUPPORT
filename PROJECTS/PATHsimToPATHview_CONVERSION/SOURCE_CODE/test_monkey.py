import sys
sys.path.append('d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/src')
from pathsim import Subsystem, Interface
I = Interface()

_orig = Subsystem.__init__
def _new(self, blocks=None, *a, **k):
    while isinstance(blocks, str):
        try:
            nb = eval(blocks, globals())
            if nb == blocks: break
            blocks = nb
        except: break
    _orig(self, blocks, *a, **k)

Subsystem.__init__ = _new

try:
    s1 = Subsystem(blocks='\"[I]\"')
    s2 = Subsystem(blocks='[I]')
    print('Success!', len(s1.blocks), len(s2.blocks))
except Exception as e:
    print('Failed!', e)