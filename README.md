# Verilog Wishbone Components Readme

For more information and updates: http://alexforencich.com/wiki/en/verilog/wishbone/start

GitHub repository: https://github.com/alexforencich/verilog-wishbone

## Introduction

Collection of Wishbone bus components.  Most components are fully
parametrizable in interface widths.  Includes full MyHDL testbench with
intelligent bus cosimulation endpoints.

## Documentation

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

    rtl/wb_async_reg.v              : Asynchronous register
    rtl/wb_dp_ram.v                 : Dual port RAM
    rtl/wb_mux_2.v                  : 2 port WB mux
    rtl/wb_mux.py                   : WB mux generator
    rtl/wb_ram.v                    : Single port RAM
    rtl/wb_reg.v                    : Register

## Testing

Running the included testbenches requires MyHDL and Icarus Verilog.  Make sure
that myhdl.vpi is installed properly for cosimulation to work correctly.  The
testbenches can be run with a Python test runner like nose or py.test, or the
individual test scripts can be run with python directly.

### Testbench Files

    tb/test_wb.py           : MyHDL testbench for master and RAM model
    tb/test_wb_async_reg.py : MyHDL testbench for wb_async_reg module
    tb/test_wb_async_reg.v  : Verilog toplevel file for wb_async_reg cosimulation
    tb/test_wb_dp_ram.py    : MyHDL testbench for wb_dp_ram module
    tb/test_wb_dp_ram.v     : Verilog toplevel file for wb_dp_ram cosimulation
    tb/test_wb_mux_2.py     : MyHDL testbench for wb_mux_2 module
    tb/test_wb_mux_2.v      : Verilog toplevel file for wb_mux_2 cosimulation
    tb/test_wb_ram.py       : MyHDL testbench for wb_ram module
    tb/test_wb_ram.v        : Verilog toplevel file for wb_ram cosimulation
    tb/test_wb_ram_model.py : MyHDL testbench for RAM model
    tb/test_wb_reg.py       : MyHDL testbench for wb_reg module
    tb/test_wb_reg.v        : Verilog toplevel file for wb_reg cosimulation
    tb/wb.py                : MyHDL Wishbone master model and RAM model
