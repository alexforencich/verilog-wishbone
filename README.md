# Verilog Wishbone Components Readme

For more information and updates: http://alexforencich.com/wiki/en/verilog/wishbone/start

GitHub repository: https://github.com/alexforencich/verilog-wishbone

## Introduction

Collection of Wishbone bus components.  Most components are fully
parametrizable in interface widths.  Includes full MyHDL testbench with
intelligent bus cosimulation endpoints.

## Documentation

### arbiter module

General-purpose parametrizable arbiter.  Supports priority and round-robin
arbitration.  Supports blocking until request release or acknowledge. 

### axis_wb_master module

AXI Stream Wishbone master.  Intended to be used to bridge a streaming
or packet-based protocol (serial, ethernet, etc.) to a Wishbone bus.

### priority_encoder module

Parametrizable priority encoder.

### wb_adapter module

Width adapter module to bridge wishbone buses of differing widths.  The module
is parametrizable, but their are certain restrictions.  First, the bus word
widths must be identical (same data bus width per select line).  Second, the
bus widths must be related by an integer multiple (e.g. 2 words and 6 words,
but not 4 words and 6 words).

### wb_arbiter_N module

Parametrizable arbiter module to enable sharing between multiple masters.

Can be generated with arbitrary port counts with wb_arbiter.py.

### wb_async_reg module

Asynchronous register module for clock domain crossing with parametrizable
data and address interface widths.  Uses internal synchronization to pass
wishbone bus cycles across clock domain boundaries.

### wb_dp_ram module

Dual-port, dual-clock RAM with parametrizable data and address interface
widths.

### wb_mux_N module

Wishbone multiplexer with parametrizable data and address interface widths.

Can be generated with arbitrary port counts with wb_mux.py.

### wb_ram module

RAM with parametrizable data and address interface widths.

### wb_reg module

Synchronous register with parametrizable data and address interface widths.
Registers all wishbone signals.  Used to improve timing for long routes.

### Source Files

    arbiter.v                   : General-purpose parametrizable arbiter
    axis_wb_master.v            : AXI Stream Wishbone master
    priority_encoder.v          : Parametrizable priority encoder
    wb_adapter.v                : Parametrizable bus width adapter
    wb_arbiter.py               : Arbiter generator
    wb_arbiter_2.py             : 2 port WB arbiter
    wb_async_reg.v              : Asynchronous register
    wb_dp_ram.v                 : Dual port RAM
    wb_mux.py                   : WB mux generator
    wb_mux_2.v                  : 2 port WB mux
    wb_ram.v                    : Single port RAM
    wb_reg.v                    : Register

## Testing

Running the included testbenches requires MyHDL and Icarus Verilog.  Make sure
that myhdl.vpi is installed properly for cosimulation to work correctly.  The
testbenches can be run with a Python test runner like nose or py.test, or the
individual test scripts can be run with python directly.

### Testbench Files

    tb/axis_ep.py           : MyHDL AXI Stream endpoints
    tb/wb.py                : MyHDL Wishbone master model and RAM model
