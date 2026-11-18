"""hwbench: standard-cell benchmarks of XORFlux and BoolFlux circuits against NIST's.

Modules:
  design     circuit files -> designs (gates, port order, reference function, NIST metrics)
  verilog    RTL, reference (spec) and testbench Verilog for a design
  liberty    a small Liberty reader: cell areas, pins, functions; function evaluation
  netlist    structural Verilog netlists: parse, simulate through Liberty functions, activity
  platforms  Nangate45 and SKY130HD settings, read from the pinned OpenROAD-flow-scripts platforms
  flow       Yosys synthesis (preserve / free), OpenROAD STA, placement and routing, checks
  report     results tables

Standard library only; the tools are run as subprocesses (see hardware/tools/install.sh).
"""
