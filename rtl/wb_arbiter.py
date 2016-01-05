#!/usr/bin/env python
"""
Generates a Wishbone arbiter with the specified number of ports
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
        name = "wb_arbiter_{0}".format(ports)

    if output is None:
        output = name + ".v"

    print("Opening file '{0}'...".format(output))

    output_file = open(output, 'w')

    print("Generating {0} port Wishbone arbiter {1}...".format(ports, name))

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
 * Wishbone {{n}} port arbiter
 */
module {{name}} #
(
    parameter DATA_WIDTH = 32,                    // width of data bus in bits (8, 16, 32, or 64)
    parameter ADDR_WIDTH = 32,                    // width of address bus in bits
    parameter SELECT_WIDTH = (DATA_WIDTH/8),      // width of word select bus (1, 2, 4, or 8)
    parameter ARB_TYPE = "PRIORITY",              // arbitration type: "PRIORITY" or "ROUND_ROBIN"
    parameter LSB_PRIORITY = "HIGH"               // LSB priority: "LOW", "HIGH"
)
(
    input  wire                    clk,
    input  wire                    rst,
{%- for p in ports %}

    /*
     * Wishbone master {{p}} input
     */
    input  wire [ADDR_WIDTH-1:0]   wbm{{p}}_adr_i,    // ADR_I() address input
    input  wire [DATA_WIDTH-1:0]   wbm{{p}}_dat_i,    // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbm{{p}}_dat_o,    // DAT_O() data out
    input  wire                    wbm{{p}}_we_i,     // WE_I write enable input
    input  wire [SELECT_WIDTH-1:0] wbm{{p}}_sel_i,    // SEL_I() select input
    input  wire                    wbm{{p}}_stb_i,    // STB_I strobe input
    output wire                    wbm{{p}}_ack_o,    // ACK_O acknowledge output
    output wire                    wbm{{p}}_err_o,    // ERR_O error output
    output wire                    wbm{{p}}_rty_o,    // RTY_O retry output
    input  wire                    wbm{{p}}_cyc_i,    // CYC_I cycle input
{%- endfor %}

    /*
     * Wishbone slave output
     */
    output wire [ADDR_WIDTH-1:0]   wbs_adr_o,     // ADR_O() address output
    input  wire [DATA_WIDTH-1:0]   wbs_dat_i,     // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbs_dat_o,     // DAT_O() data out
    output wire                    wbs_we_o,      // WE_O write enable output
    output wire [SELECT_WIDTH-1:0] wbs_sel_o,     // SEL_O() select output
    output wire                    wbs_stb_o,     // STB_O strobe output
    input  wire                    wbs_ack_i,     // ACK_I acknowledge input
    input  wire                    wbs_err_i,     // ERR_I error input
    input  wire                    wbs_rty_i,     // RTY_I retry input
    output wire                    wbs_cyc_o      // CYC_O cycle output
);

wire [{{n-1}}:0] request;
wire [{{n-1}}:0] grant;
{% for p in ports %}
assign request[{{p}}] = wbm{{p}}_cyc_i;
{%- endfor %}
{% for p in ports %}
wire wbm{{p}}_sel = grant[{{p}}] & grant_valid;
{%- endfor %}
{%- for p in ports %}

// master {{p}}
assign wbm{{p}}_dat_o = wbs_dat_i;
assign wbm{{p}}_ack_o = wbs_ack_i & wbm{{p}}_sel;
assign wbm{{p}}_err_o = wbs_err_i & wbm{{p}}_sel;
assign wbm{{p}}_rty_o = wbs_rty_i & wbm{{p}}_sel;
{%- endfor %}

// slave
assign wbs_adr_o = {% for p in ports %}wbm{{p}}_sel ? wbm{{p}}_adr_i :
                   {% endfor %}{ADDR_WIDTH{1'b0}};

assign wbs_dat_o = {% for p in ports %}wbm{{p}}_sel ? wbm{{p}}_dat_i :
                   {% endfor %}{DATA_WIDTH{1'b0}};

assign wbs_we_o = {% for p in ports %}wbm{{p}}_sel ? wbm{{p}}_we_i :
                  {% endfor %}1'b0;

assign wbs_sel_o = {% for p in ports %}wbm{{p}}_sel ? wbm{{p}}_sel_i :
                   {% endfor %}{SELECT_WIDTH{1'b0}};

assign wbs_stb_o = {% for p in ports %}wbm{{p}}_sel ? wbm{{p}}_stb_i :
                   {% endfor %}1'b0;

assign wbs_cyc_o = {% for p in ports %}wbm{{p}}_sel ? 1'b1 :
                   {% endfor %}1'b0;

// arbiter instance
arbiter #(
    .PORTS({{n}}),
    .TYPE(ARB_TYPE),
    .BLOCK("REQUEST"),
    .LSB_PRIORITY(LSB_PRIORITY)
)
arb_inst (
    .clk(clk),
    .rst(rst),
    .request(request),
    .acknowledge(),
    .grant(grant),
    .grant_valid(grant_valid),
    .grant_encoded()
);

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

