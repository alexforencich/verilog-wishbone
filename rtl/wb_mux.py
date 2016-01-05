#!/usr/bin/env python
"""
Generates a Wishbone multiplexer with the specified number of ports
"""

from __future__ import print_function

import argparse
import math
from jinja2 import Template

def main():
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument('-p', '--ports',  type=int, default=2, help="number of ports")
    parser.add_argument('-n', '--name',   type=str, help="module name")
    parser.add_argument('-o', '--output', type=str, help="output file name")

    args = parser.parse_args()

    try:
        generate(**args.__dict__)
    except IOError as ex:
        print(ex)
        exit(1)

def generate(ports=2, name=None, output=None):
    if name is None:
        name = "wb_mux_{0}".format(ports)

    if output is None:
        output = name + ".v"

    print("Opening file '{0}'...".format(output))

    output_file = open(output, 'w')

    print("Generating {0} port Wishbone mux {1}...".format(ports, name))

    select_width = int(math.ceil(math.log(ports, 2)))

    t = Template(u"""/*

Copyright (c) 2015-2016 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

*/

// Language: Verilog 2001

`timescale 1 ns / 1 ps

/*
 * Wishbone {{n}} port multiplexer
 */
module {{name}} #
(
    parameter DATA_WIDTH = 32,                    // width of data bus in bits (8, 16, 32, or 64)
    parameter ADDR_WIDTH = 32,                    // width of address bus in bits
    parameter SELECT_WIDTH = (DATA_WIDTH/8)       // width of word select bus (1, 2, 4, or 8)
)
(
    input  wire                    clk,
    input  wire                    rst,

    /*
     * Wishbone master input
     */
    input  wire [ADDR_WIDTH-1:0]   wbm_adr_i,     // ADR_I() address input
    input  wire [DATA_WIDTH-1:0]   wbm_dat_i,     // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbm_dat_o,     // DAT_O() data out
    input  wire                    wbm_we_i,      // WE_I write enable input
    input  wire [SELECT_WIDTH-1:0] wbm_sel_i,     // SEL_I() select input
    input  wire                    wbm_stb_i,     // STB_I strobe input
    output wire                    wbm_ack_o,     // ACK_O acknowledge output
    output wire                    wbm_err_o,     // ERR_O error output
    output wire                    wbm_rty_o,     // RTY_O retry output
    input  wire                    wbm_cyc_i,     // CYC_I cycle input
    {%- for p in ports %}

    /*
     * Wishbone slave {{p}} output
     */
    output wire [ADDR_WIDTH-1:0]   wbs{{p}}_adr_o,    // ADR_O() address output
    input  wire [DATA_WIDTH-1:0]   wbs{{p}}_dat_i,    // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbs{{p}}_dat_o,    // DAT_O() data out
    output wire                    wbs{{p}}_we_o,     // WE_O write enable output
    output wire [SELECT_WIDTH-1:0] wbs{{p}}_sel_o,    // SEL_O() select output
    output wire                    wbs{{p}}_stb_o,    // STB_O strobe output
    input  wire                    wbs{{p}}_ack_i,    // ACK_I acknowledge input
    input  wire                    wbs{{p}}_err_i,    // ERR_I error input
    input  wire                    wbs{{p}}_rty_i,    // RTY_I retry input
    output wire                    wbs{{p}}_cyc_o,    // CYC_O cycle output

    /*
     * Wishbone slave {{p}} address configuration
     */
    input  wire [ADDR_WIDTH-1:0]   wbs{{p}}_addr,     // Slave address prefix
    input  wire [ADDR_WIDTH-1:0]   wbs{{p}}_addr_msk{% if not loop.last %},{% else %} {% endif %} // Slave address prefix mask
    {%- endfor %}
);
{% for p in ports %}
wire wbs{{p}}_match = ~|((wbm_adr_i ^ wbs{{p}}_addr) & wbs{{p}}_addr_msk);
{%- endfor %}
{% for p in ports %}
wire wbs{{p}}_sel = wbs{{p}}_match{% if p > 0 %} & ~({% for q in range(p) %}wbs{{q}}_match{% if not loop.last %} | {% endif %}{% endfor %}){% endif %};
{%- endfor %}

wire master_cycle = wbm_cyc_i & wbm_stb_i;

wire select_error = ~({% for p in ports %}wbs{{p}}_sel{% if not loop.last %} | {% endif %}{% endfor %}) & master_cycle;

// master
assign wbm_dat_o = {% for p in ports %}wbs{{p}}_sel ? wbs{{p}}_dat_i :
                   {% endfor %}{DATA_WIDTH{1'b0}};

assign wbm_ack_o = {% for p in ports %}wbs{{p}}_ack_i{% if not loop.last %} |
                   {% endif %}{% endfor %};

assign wbm_err_o = {% for p in ports %}wbs{{p}}_err_i |
                   {% endfor %}select_error;

assign wbm_rty_o = {% for p in ports %}wbs{{p}}_rty_i{% if not loop.last %} |
                   {% endif %}{% endfor %};
{% for p in ports %}
// slave {{p}}
assign wbs{{p}}_adr_o = wbm_adr_i;
assign wbs{{p}}_dat_o = wbm_dat_i;
assign wbs{{p}}_we_o = wbm_we_i & wbs{{p}}_sel;
assign wbs{{p}}_sel_o = wbm_sel_i;
assign wbs{{p}}_stb_o = wbm_stb_i & wbs{{p}}_sel;
assign wbs{{p}}_cyc_o = wbm_cyc_i & wbs{{p}}_sel;
{% endfor %}

endmodule

""")
    
    output_file.write(t.render(
        n=ports,
        w=select_width,
        name=name,
        ports=range(ports)
    ))
    
    print("Done")

if __name__ == "__main__":
    main()

