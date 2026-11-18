"""The flows: Verilog, checks, Yosys synthesis, OpenROAD timing/power/placement/routing.

One *job* is (design, platform, flow).  Flows (same Yosys, ABC, OpenROAD and constraints for all):

  preserve    every gate of the circuit file becomes one 2-input cell (AND2/XOR2/XNOR2, INV for
              NOT) of drive strength 1; no logic optimisation.  The cell counts are asserted.
  free        Yosys ``synth -flatten`` then ABC mapping to the whole library (``abc -liberty``,
              Yosys's default ABC script: delay-oriented mapping ``&nf`` then buffering and
              gate sizing; ORFS's don't-use list, ORFS's driver and load).
  free-area   the same, but the mapper's delay target relaxed by 1000% (``&nf -R 1000``) and no
              buffering or sizing: area-oriented.

Physical flow (OpenROAD, every job): one buffer after each input port (``buffer_ports -inputs``),
floorplan at 40% core utilisation, ORFS tracks and tap cells, pin placement and global placement
in ORFS's order, detailed placement, global and detailed routing, RC extraction with OpenRCX.  Timing and power are reported after synthesis (no wires), after
placement (estimated wires) and after routing (extracted parasitics).  No buffering, sizing or
timing repair is run, so apart from the input buffers the cells placed and routed are the cells
synthesis chose (checked).  No power grid
is built; power numbers are OpenSTA's with exact zero-delay switching activity (netlist.py).

Checks, all of which must pass for a job's numbers to be reported:
  RTL      Icarus simulation of all 2^n inputs (n <= 16; else 65,536 random inputs and the unit
           vectors) against the reference table; formal proof of RTL == reference (Yosys miter,
           ABC ``&cec``, see formal_equiv)
  mapped   simulation through Liberty functions (netlist.py) of the same inputs; formal proof
           of the mapped netlist (cells read from the Liberty file) == reference
  routed   the same two checks on OpenROAD's routed netlist; detailed routing with 0 DRC errors
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import time

from . import design as D, liberty as L, netlist as N, platforms as P, verilog as V

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BUILD = pathlib.Path(os.environ.get('HWBENCH_BUILD', ROOT / 'build'))
FLOWS = ('preserve', 'free', 'free-area')

# Yosys's default ABC script for Liberty mapping, without the final sizing, and with the delay
# target of the mapper relaxed by 1000% so that it recovers area instead.
ABC_AREA_SCRIPT = ('+strash;&get,-n;&fraig,-x;&put;scorr;dc2;dretime;strash;&get,-n;&dch,-f;'
                   '&nf,-R,1000;&put')

PERIOD_NS = 10.0          # virtual clock: 100 MHz reference for power; delay = period - worst slack
UTILIZATION = 40          # % core utilisation
CORE_SPACE_UM = 2.0
INPUT_ACTIVITY = 0.5      # toggles per cycle of each input (independent random inputs)


class CheckFailed(RuntimeError):
    pass


def tool(env, args, cwd, log, timeout=3600):
    """Run a tool of a micromamba environment; output to ``log``; raise on failure.

    The executable is called from the environment's bin/ folder (not through ``micromamba run``,
    whose lock fails under many parallel jobs)."""
    prefix = P.TOOLS / 'mamba' / 'envs' / env
    envd = dict(os.environ, CONDA_PREFIX=str(prefix),
                PATH='%s:%s' % (prefix / 'bin', os.environ.get('PATH', '')))
    with open(log, 'w') as f:
        r = subprocess.run([str(prefix / 'bin' / args[0])] + list(args[1:]), cwd=cwd, stdout=f,
                           stderr=subprocess.STDOUT, env=envd, timeout=timeout)
    if r.returncode:
        tail = pathlib.Path(log).read_text()[-2000:]
        raise RuntimeError('%s failed (%d), log %s:\n%s' % (args[0], r.returncode, log, tail))
    return pathlib.Path(log).read_text()


def versions():
    f = P.TOOLS / 'VERSIONS'
    out = {}
    if f.exists():
        for line in f.read_text().splitlines():
            if line.startswith('#') or not line.strip():
                if line.startswith('# explicit'):
                    break
                continue
            out[line.split()[0]] = line.strip()
    return out


# ---- per design: Verilog and RTL checks ---------------------------------------------------

def design_dir(d):
    return BUILD / d.id


JOB_MODULES = ('design.py', 'flow.py', 'liberty.py', 'netlist.py', 'platforms.py', 'verilog.py')


def code_hash():
    """SHA-256 of the code a job's results depend on (not the tables' code): results of other
    code are not reused."""
    h = hashlib.sha256()
    for name in JOB_MODULES:
        h.update(name.encode() + b'\0' + (HERE / name).read_bytes())
    for f in sorted((HERE.parents[1] / 'circuits' / 'boolcirc').glob('*.py')):
        h.update(f.name.encode() + b'\0' + f.read_bytes())       # the reference functions
    return h.hexdigest()


def fingerprint(*parts):
    h = hashlib.sha256(code_hash().encode())
    vf = P.TOOLS / 'VERSIONS'                    # tool versions, not the install date
    h.update(''.join(l for l in vf.read_text().splitlines(True) if not l.startswith('#')).encode()
             if vf.exists() else b'')
    for x in parts:
        h.update(b'\0' + str(x).encode())
    return h.hexdigest()[:16]


def prepare(d):
    """Write rtl.v, spec.v, tb.v and vectors; check the RTL (simulation and formal proof)."""
    out = design_dir(d)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'rtl.v').write_text(V.rtl(d))
    (out / 'spec.v').write_text(V.spec(d))
    xs = V.vectors(d)
    vx, vy = V.vector_files(d, xs)
    (out / 'vec_x.hex').write_text(vx)
    (out / 'vec_y.hex').write_text(vy)
    (out / 'tb.v').write_text(V.testbench(d, len(xs)))
    tool('yosys', ['iverilog', '-g2005', '-o', 'tb.vvp', 'tb.v', 'rtl.v'], out, out / 'iverilog.log')
    log = tool('yosys', ['vvp', '-n', 'tb.vvp'], out, out / 'sim.log')
    m = re.search(r'CHECKED (\d+) ERRORS (\d+)', log)
    if not m or int(m.group(2)) or int(m.group(1)) != len(xs):
        raise CheckFailed('%s: RTL simulation: %s' % (d.id, log[-500:]))
    formal_equiv(out, 'rtl.v', out / 'rtl_cec.log', liberty=None)
    return {'sim_vectors': len(xs), 'sim_exhaustive': len(xs) == 1 << d.n_in, 'formal': 'proved'}


def formal_equiv(cwd, netlist, log, liberty=None):
    """Formal proof that module ``dut`` of ``netlist`` equals module ``spec`` of spec.v.

    Yosys builds the miter (reading the cells' functions from the Liberty file when given) and
    writes it as an AIG; ABC's ``&cec`` proves that the miter output is constant 0, i.e. that the
    two modules agree on every input.  (Yosys's own ``sat`` proves the S-boxes too, but takes
    minutes on the 32-input XOR miters of MixColumns; ABC takes about a second.)"""
    cwd = pathlib.Path(cwd)
    stem = pathlib.Path(netlist).stem
    cmds = []
    if liberty:
        cmds.append('read_liberty -ignore_miss_func -ignore_miss_dir -ignore_miss_data_latch %s'
                    % liberty)
    spec = cwd / 'spec.v'
    if not spec.exists():
        spec = cwd.parents[1] / 'spec.v'
    aig = '%s_miter.aig' % stem
    cmds += ['read_verilog %s' % spec, 'read_verilog %s' % netlist, 'proc -norom',
             'miter -equiv -flatten spec dut miter', 'hierarchy -top miter', 'flatten -noscopeinfo',
             # the reference case table is full, so its multiplexer default (x) is unreachable;
             # undriven nets of a netlist would also become 0, but the Liberty simulation
             # refuses those before this proof runs
             'delete t:$scopeinfo', 'setundef -zero', 'techmap', 'opt_clean', 'aigmap', 'opt_clean', 'write_aiger -zinit %s' % aig]
    tool('yosys', ['yosys', '-p', '; '.join(cmds)], cwd, '%s.yosys.log' % log)
    text = tool('yosys', ['yosys-abc', '-c', '&r %s; &ps; &cec -m' % aig], cwd, log)
    m = re.search(r'i/o\s*=\s*(\d+)/\s*(\d+)', text)
    if not m or int(m.group(2)) != 1:
        raise CheckFailed('miter %s is not a single-output miter, see %s' % (aig, log))
    if 'NOT EQUIVALENT' in text:
        raise CheckFailed('not equivalent (ABC &cec), see %s' % log)
    if 'Networks are equivalent' not in text:
        raise CheckFailed('equivalence not proved, see %s' % log)
    return int(m.group(1))


# ---- per job: synthesis -----------------------------------------------------------------

def cellmap(p):
    """Yosys techmap file: Yosys's internal 2-input gates -> the platform's cells."""
    pins = {'AND': ('A', 'B'), 'XOR': ('A', 'B'), 'XNOR': ('A', 'B'), 'NOT': ('A',)}
    out = []
    for op, (cell, *cp) in p.gate_cells.items():
        ins, o = cp[:-1], cp[-1]
        ports = ', '.join('input %s' % a for a in pins[op]) + ', output Y'
        conns = ', '.join('.%s(%s)' % (c, a) for c, a in zip(ins, pins[op])) + ', .%s(Y)' % o
        out.append('module \\$_%s_ (%s);\n  %s _TECHMAP_REPLACE_ (%s);\nendmodule' % (
            op, ports, cell, conns))
    return '\n'.join(out) + '\n'


def abc_constraints(p, lib):
    return 'set_driving_cell %s\nset_load %g\n' % (p.buf[0], lib.cap_in_lib_units(p.load_ff))


def synth(d, p, flow, out, lib):
    libf = p.path(p.lib)
    common_tail = ['hilomap -singleton -hicell %s %s -locell %s %s' % (p.tie_hi + p.tie_lo),
                   'opt_clean -purge', 'insbuf -buf %s %s %s' % p.buf, 'opt_clean -purge',
                   'check -assert',
                   'write_verilog -noattr -noexpr -nohex -nodec mapped.v',
                   'tee -o stat.txt stat -liberty %s' % libf]
    rtl = design_dir(d) / 'rtl.v'
    if flow == 'preserve':
        (out / 'cellmap.v').write_text(cellmap(p))
        cmds = ['read_liberty -lib %s' % libf, 'read_verilog %s' % rtl, 'hierarchy -check -top dut',
                'proc', 'flatten', 'techmap', 'opt_clean', 'techmap -map cellmap.v'] + common_tail
    else:
        (out / 'abc.constr').write_text(abc_constraints(p, lib))
        dont = ' '.join('-dont_use %s' % c for c in p.dont_use)
        script = ' -script %s' % ABC_AREA_SCRIPT if flow == 'free-area' else ''
        cmds = ['read_liberty -lib %s' % libf, 'read_verilog %s' % rtl,
                'synth -top dut -flatten', 'abc -liberty %s -constr abc.constr %s%s'
                % (libf, dont, script)] + common_tail
    (out / 'synth.ys').write_text('\n'.join(cmds) + '\n')
    tool('yosys', ['yosys', '-s', 'synth.ys'], out, out / 'synth.log')


# ---- per job: OpenROAD --------------------------------------------------------------------

def sdc(p, lib):
    return '\n'.join([
        'create_clock -name vclk -period %g' % PERIOD_NS,
        'set_input_delay 0 -clock vclk [all_inputs]',
        'set_output_delay 0 -clock vclk [all_outputs]',
        'set_driving_cell -lib_cell %s -pin %s [all_inputs]' % (p.buf[0], p.buf[2]),
        'set_load %g [all_outputs]' % lib.cap_in_lib_units(p.load_ff), ''])


def activity_tcl(nl, lib, sim, physical):
    act = N.activity(sim)
    lines = ['set_power_activity -input -activity %g -duty 0.5' % INPUT_ACTIVITY]
    for inst in nl.instances:
        c = lib.cells[inst.cell]
        if inst.cell.startswith(tuple(physical)):
            continue
        for pin in c.outputs:
            n = inst.pins.get(pin.name)
            if n in act:
                a, duty = act[n]
                lines.append('set_power_activity -pins {%s/%s} -activity %.6f -duty %.6f'
                             % (inst.name, pin.name, a, duty))
    return '\n'.join(lines) + '\n'


PNR_TCL = r'''
# generated by hardware/hwbench/flow.py
set_thread_count 1
read_lef {tech_lef}
read_lef {sc_lef}
read_liberty {lib}
read_verilog mapped.v
link_design dut
read_sdc constraints.sdc
source activity.tcl
set_dont_use {{{dont_use}}}
# a buffer between each input port and the logic, as ORFS does (buffer_ports skips an input that
# already drives one buffer): every input net then drives one buffer, its switching is counted,
# and the driving cell sees one buffer input
{port_buffer_dont_use}
buffer_ports -inputs

proc hwb_report {{stage}} {{
  set ws [sta::worst_slack -max]
  puts "HWB $stage worst_slack $ws"
  report_checks -path_delay max -fields {{slew cap input_pins fanout}} -digits 4 > $stage.timing.rpt
  report_power -digits 6 > $stage.power.rpt
  report_check_types -max_slew -max_capacitance -max_fanout -violators > $stage.drv.rpt
  report_design_area
}}

hwb_report synth

initialize_floorplan -utilization {util} -aspect_ratio 1 -core_space {space} -site {site}
source {platform}/make_tracks.tcl
source {platform}/tapcell.tcl
# pins as ORFS places them: random, global placement without them, pins placed next to their
# cells, then global placement again
place_pins -random -hor_layers {io_h} -ver_layers {io_v}
global_placement -skip_io -density {density}
place_pins -hor_layers {io_h} -ver_layers {io_v}
global_placement -density {density}
detailed_placement
check_placement
source {platform}/setRC.tcl
estimate_parasitics -placement
hwb_report place

set_routing_layers -signal {min_route}-{max_route}
{gr_adjust}
global_route
detailed_route -output_drc route_drc.rpt -verbose 1
extract_parasitics -ext_model_file {platform}/rcx_patterns.rules
write_spef routed.spef
read_spef routed.spef
hwb_report route
puts "HWB die_area [ord::get_die_area]"
puts "HWB core_area [ord::get_core_area]"
write_verilog routed.v
write_def routed.def
exit
'''

# buffer_ports takes the weakest buffer; on SKY130 that would be a clock buffer (clkbuf_1)
PORT_BUFFER_DONT_USE = {
    'sky130hd': 'set_dont_use [get_lib_cells {sky130_fd_sc_hd__clkbuf_* sky130_fd_sc_hd__dlygate* '
                'sky130_fd_sc_hd__dlymetal* sky130_fd_sc_hd__clkdlybuf*}]',
}

GR_ADJUST = {
    'nangate45': 'set_global_routing_layer_adjustment metal2-metal3 0.5\n'
                 'set_global_routing_layer_adjustment metal4-metal10 0.25',
    'sky130hd': 'set_global_routing_layer_adjustment met1-met5 0.2',
}


def pnr(p, out, lib):
    tcl = PNR_TCL.format(tech_lef=p.path(p.tech_lef), sc_lef=p.path(p.sc_lef), lib=p.path(p.lib),
                         util=UTILIZATION, space=CORE_SPACE_UM, site=p.site, platform=p.dir,
                         io_h=p.io_h, io_v=p.io_v, density=min(0.95, UTILIZATION / 100 + 0.2),
                         min_route=p.min_route, max_route=p.max_route, gr_adjust=GR_ADJUST[p.name],
                         dont_use=' '.join(p.dont_use),
                         port_buffer_dont_use=PORT_BUFFER_DONT_USE.get(p.name, ''))
    (out / 'pnr.tcl').write_text(tcl)
    return tool('openroad', ['openroad', '-no_init', '-no_splash', '-exit', 'pnr.tcl'], out,
                out / 'pnr.log', timeout=7200)


def parse_power(text):
    m = re.search(r'^Total\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)', text, re.M)
    if not m:
        return None
    i, s, l, t = (float(v) for v in m.groups())
    return {'internal_W': i, 'switching_W': s, 'leakage_W': l, 'total_W': t}


def count_drv(text):
    return len(re.findall(r'\(VIOLATED\)|VIOLATED', text))


def port_buffers(nl, lib, d):
    """The buffers buffer_ports inserted (named inputN): {cell: count}.

    buffer_ports skips an input that already drives a single buffer (ABC adds some in the free
    flows), so there are at most n of them, each on its own input port."""
    out, ports = {}, []
    for inst in nl.instances:
        if not re.fullmatch(r'input\d+', inst.name):
            continue
        c = lib.cells.get(inst.cell)
        src = inst.pins.get(c.inputs[0].name, '') if c and len(c.inputs) == 1 else ''
        if not (c and len(c.outputs) == 1 and c.outputs[0].function.strip('() ') == c.inputs[0].name
                and re.fullmatch(r'x\[\d+\]', src)):
            raise CheckFailed('%s is not a buffer on an input port' % inst.name)
        out[inst.cell] = out.get(inst.cell, 0) + 1
        ports.append(src)
    if len(set(ports)) != len(ports) or len(ports) > d.n_in:
        raise CheckFailed('input buffers %s on ports %s' % (out, ports))
    return out


# ---- a job ---------------------------------------------------------------------------------

def job_dir(d, platform, flow):
    return design_dir(d) / platform / flow


def run_job(path, platform, flow, force=False):
    """Run one job; returns the metrics dict (also written to metrics.json in the job folder)."""
    t0 = time.time()
    d = D.load(path)
    p = P.get(platform)
    out = job_dir(d, platform, flow)
    mfile = out / 'metrics.json'
    fp = fingerprint(d.sha256, platform, flow, p.lib_sha256())
    if mfile.exists() and not force:
        old = json.loads(mfile.read_text())
        if old.get('fingerprint') == fp:
            return old
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    lib = L.load(p.path(p.lib), cache_dir=BUILD / '_liberty')
    _, rtl_check = prepare_design(path)

    synth(d, p, flow, out, lib)
    nl = N.parse((out / 'mapped.v').read_text())
    xs = V.vectors(d)
    sim = N.simulate(nl, lib, d, xs, p.physical)
    if sim.mismatches:
        raise CheckFailed('%s %s %s: mapped netlist differs from the reference: %s'
                          % (d.id, platform, flow, sim.first_mismatch))
    if flow == 'preserve':
        want = V.expected_cells(d)
        got = {op: sim.cells.get(p.gate_cells[op][0], 0) for op in want}
        extra = {c: k for c, k in sim.cells.items()
                 if c not in [p.gate_cells[o][0] for o in want] and c != p.buf[0]}
        if got != want or extra:
            raise CheckFailed('%s %s preserve: cells %s %s, circuit has %s'
                              % (d.id, platform, got, extra, want))
    formal_equiv(out, 'mapped.v', out / 'mapped_cec.log', liberty=p.path(p.lib))

    (out / 'constraints.sdc').write_text(sdc(p, lib))
    (out / 'activity.tcl').write_text(activity_tcl(nl, lib, sim, p.physical))
    log = pnr(p, out, lib)

    stages = {}
    for st in ('synth', 'place', 'route'):
        m = re.search(r'^HWB %s worst_slack (\S+)' % st, log, re.M)
        if not m:
            raise RuntimeError('no timing for stage %s in %s' % (st, out / 'pnr.log'))
        slack = float(m.group(1))
        power = parse_power((out / ('%s.power.rpt' % st)).read_text())
        stages[st] = {'delay_ns': round(PERIOD_NS - slack, 6), 'power': power,
                      'drv_violations': count_drv((out / ('%s.drv.rpt' % st)).read_text())}
    drc = re.findall(r'Number of violations\s*=\s*(\d+)', log)
    wl = re.findall(r'Total wire length\s*=\s*([\d.]+)\s*um', log)
    die = re.search(r'^HWB die_area (.*)$', log, re.M).group(1).split()
    core = re.search(r'^HWB core_area (.*)$', log, re.M).group(1).split()
    if not drc or int(drc[-1]):
        raise CheckFailed('%s %s %s: detailed routing left %s DRC violations'
                          % (d.id, platform, flow, drc[-1] if drc else '?'))

    rnl = N.parse((out / 'routed.v').read_text())
    rsim = N.simulate(rnl, lib, d, xs, p.physical)
    if rsim.mismatches:
        raise CheckFailed('%s %s %s: routed netlist differs from the reference: %s'
                          % (d.id, platform, flow, rsim.first_mismatch))
    port_bufs = port_buffers(rnl, lib, d)
    logic = dict(rsim.cells)
    for c, k in port_bufs.items():
        logic[c] -= k
        if not logic[c]:
            del logic[c]
    if logic != sim.cells:
        raise CheckFailed('%s %s %s: placement or routing changed the logic cells'
                          % (d.id, platform, flow))
    # The formal proof reads the routed netlist without its physical-only cells (taps have no
    # logic and some are not in the Liberty file).
    text = (out / 'routed.v').read_text()
    phys = re.compile(r'^\s*(%s)\S*\s+\S+\s*\([^;]*\);' % '|'.join(map(re.escape, p.physical)),
                      re.M)
    (out / 'routed_logic.v').write_text(phys.sub('', text))
    formal_equiv(out, 'routed_logic.v', out / 'routed_cec.log', liberty=p.path(p.lib))

    def rect_area(v):
        x0, y0, x1, y1 = (float(a) for a in v)
        return (x1 - x0) * (y1 - y0)

    area = sim.area_logic
    res = {
        'fingerprint': fp, 'design': d.id, 'name': d.name, 'origin': d.origin, 'kind': d.kind, 'function': d.function,
        'file': d.path.relative_to(D.REPO).as_posix(), 'sha256': d.sha256, 'metrics': d.metrics,
        'platform': platform, 'flow': flow,
        'cells': sum(sim.cells.values()), 'cell_types': sim.cells,
        'area_um2': round(area, 4),
        'delay_ns': stages['synth']['delay_ns'],
        'adp_um2ns': round(area * stages['synth']['delay_ns'], 4),
        'stages': stages,
        'route': {'delay_ns': stages['route']['delay_ns'],
                  'adp_um2ns': round(area * stages['route']['delay_ns'], 4),
                  'power': stages['route']['power'],
                  'wirelength_um': float(wl[-1]) if wl else None,
                  'drc': int(drc[-1]),
                  'die_um2': round(rect_area(die), 3), 'core_um2': round(rect_area(core), 3),
                  'physical_cells': rsim.physical_cells, 'port_buffers': port_bufs},
        'checks': {'rtl': rtl_check,
                   'mapped': {'sim_vectors': sim.count, 'sim_exhaustive': sim.exhaustive,
                              'formal': 'proved'},
                   'routed': {'sim_vectors': rsim.count, 'sim_exhaustive': rsim.exhaustive,
                              'formal': 'proved', 'drc': 0}},
        'settings': {'period_ns': PERIOD_NS, 'utilization_pct': UTILIZATION,
                     'input_activity': INPUT_ACTIVITY, 'load_fF': p.load_ff,
                     'driver': p.buf[0]},
        'tools': versions(),
        'seconds': round(time.time() - t0, 1),
    }
    mfile.write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
    return res


def prepare_design(path, force=False):
    d = D.load(path)
    f = design_dir(d) / 'rtl_check.json'
    fp = fingerprint(d.sha256)
    if f.exists() and not force:
        old = json.loads(f.read_text())
        if old.pop('fingerprint', None) == fp:
            return d, old
    res = prepare(d)
    f.write_text(json.dumps(dict(res, fingerprint=fp)) + '\n')
    return d, res
