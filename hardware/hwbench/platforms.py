"""Nangate45 and SKY130HD, as OpenROAD-flow-scripts (pinned commit, see tools/install.sh) sets them up.

File names, the placement site, the I/O and routing layers, the tie and buffer cells and the
don't-use lists are those of ORFS's ``flow/platforms/<platform>/config.mk`` (the don't-use list is
read from it).  The benchmark's own choices are the 2-input cells of the structure-preserving
mapping and the timing context (driver and load), stated here once for every circuit and flow.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
from dataclasses import dataclass, field

TOOLS = pathlib.Path(os.environ.get('HWBENCH_TOOLS', pathlib.Path.home() / '.local' / 'hwbench'))
ORFS = TOOLS / 'platforms' / 'orfs' / 'flow' / 'platforms'


@dataclass
class Platform:
    name: str
    lib: str
    tech_lef: str
    sc_lef: str
    site: str
    io_h: str
    io_v: str
    min_route: str
    max_route: str
    # one cell per NIST gate type: (cell, input pins..., output pin)
    gate_cells: dict
    buf: tuple            # (cell, in, out): output buffers and the input driver
    tie_hi: tuple
    tie_lo: tuple
    load_ff: float        # output load, fF (ORFS's ABC_LOAD_IN_FF)
    physical: tuple = ()  # cell name prefixes without logic (taps, fill, decap)
    dont_use: list = field(default_factory=list)

    @property
    def dir(self):
        return ORFS / self.name

    def path(self, rel):
        return self.dir / rel

    def lib_sha256(self):
        return hashlib.sha256(self.path(self.lib).read_bytes()).hexdigest()


NANGATE45 = Platform(
    name='nangate45',
    lib='lib/NangateOpenCellLibrary_typical.lib',
    tech_lef='lef/NangateOpenCellLibrary.tech.lef',
    sc_lef='lef/NangateOpenCellLibrary.macro.mod.lef',
    site='FreePDK45_38x28_10R_NP_162NW_34O',
    io_h='metal5', io_v='metal6', min_route='metal2', max_route='metal10',
    gate_cells={'AND': ('AND2_X1', 'A1', 'A2', 'ZN'), 'XOR': ('XOR2_X1', 'A', 'B', 'Z'),
                'XNOR': ('XNOR2_X1', 'A', 'B', 'ZN'), 'NOT': ('INV_X1', 'A', 'ZN')},
    buf=('BUF_X1', 'A', 'Z'), tie_hi=('LOGIC1_X1', 'Z'), tie_lo=('LOGIC0_X1', 'Z'),
    load_ff=3.898, physical=('TAPCELL', 'FILLCELL'))

SKY130HD = Platform(
    name='sky130hd',
    lib='lib/sky130_fd_sc_hd__tt_025C_1v80.lib',
    tech_lef='lef/sky130_fd_sc_hd.tlef',
    sc_lef='lef/sky130_fd_sc_hd_merged.lef',
    site='unithd',
    io_h='met3', io_v='met2', min_route='met1', max_route='met5',
    gate_cells={'AND': ('sky130_fd_sc_hd__and2_1', 'A', 'B', 'X'),
                'XOR': ('sky130_fd_sc_hd__xor2_1', 'A', 'B', 'X'),
                'XNOR': ('sky130_fd_sc_hd__xnor2_1', 'A', 'B', 'Y'),
                'NOT': ('sky130_fd_sc_hd__inv_1', 'A', 'Y')},
    buf=('sky130_fd_sc_hd__buf_1', 'A', 'X'), tie_hi=('sky130_fd_sc_hd__conb_1', 'HI'),
    tie_lo=('sky130_fd_sc_hd__conb_1', 'LO'),
    load_ff=5.0, physical=('sky130_fd_sc_hd__tap', 'sky130_fd_sc_hd__fill',
                           'sky130_fd_sc_hd__decap'))

PLATFORMS = {p.name: p for p in (NANGATE45, SKY130HD)}


def dont_use(p):
    """DONT_USE_CELLS of ORFS's config.mk for the platform (with its line continuations)."""
    text = (p.dir / 'config.mk').read_text().replace('\\\n', ' ')
    cells = []
    for m in re.finditer(r'^\s*export\s+DONT_USE_CELLS\s*\+?=\s*(.*)$', text, re.M):
        cells += m.group(1).split()
    return cells


def get(name):
    p = PLATFORMS[name]
    if not p.dont_use:
        p.dont_use = dont_use(p)
    return p
