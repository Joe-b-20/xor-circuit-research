"""GF(4)-coordinate moves (hub/ops/gf4_lib: nbscan.current_points, gf4build.build) for either AES function.

gf4_lib prices and builds the level-3 products Q_w * R_c of an AND-depth-3 tower circuit with the tables
Q_w = Tr(w z^170), R_c = Tr(c z^84) as functions of the circuit input, z = x: true for the forward S-box,
whose inversion input is x itself (S(x) = A x^254 + 0x63).  The inverse S-box inverts z = A^-1 y + 0x05;
since inversion is an involution (0 -> 0), z(y) = S^-1(y)^254 exactly, independent of bit conventions.
install(function) rebuilds the two table sets over z(input) and installs them in the gf4_lib modules
(their module globals RT, QT), so current_points / build work unchanged on inverse circuits (U4 #1 port;
the field-intrinsic parts, point admissibility and rho, do not depend on the input map).
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
GF4 = HERE.parents[1] / 'hub' / 'ops' / 'gf4_lib'
if str(GF4) not in sys.path: sys.path.append(str(GF4))
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import aesfn                                     # noqa: E402
from boolflux.hub.common import _gmul, _gpow                   # noqa: E402

_CACHE = {}
INSTALLED = [None]


def zmap(function):
    """inversion input z as a function of the circuit input, as a list of 256 field elements"""
    if function == 'aes-sbox':
        return list(range(256))
    tab = aesfn.table(function)
    return [_gpow(tab[y], 254) for y in range(256)]


def tables(function):
    if function in _CACHE: return _CACHE[function]
    import gf4basis as G
    z = zmap(function)
    p170 = [_gpow(z[x], 170) for x in range(256)]; p84 = [_gpow(z[x], 84) for x in range(256)]
    RT = {cc: G.table(lambda x, cc=cc: G.trace(_gmul(cc, p84[x]))) for cc in range(1, 256)}
    QT = {w: G.table(lambda x, w=w: G.trace(_gmul(w, p170[x]))) for w in range(1, 256)}
    _CACHE[function] = (RT, QT)
    return RT, QT


def install(function=None):
    """set RT / QT of gf4basis, gf4build and nbscan to the tables of `function` (default: the process's)"""
    function = function or aesfn.name()
    if INSTALLED[0] == function: return
    import gf4basis, gf4build, nbscan
    RT, QT = tables(function)
    for m in (gf4basis, gf4build, nbscan):
        m.RT = RT; m.QT = QT
    INSTALLED[0] = function
