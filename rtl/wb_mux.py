#!/usr/bin/env python
"""wb_mux

Generates a Wishbone multiplexer with the specified number of ports

Usage: axis_mux [OPTION]...
  -?, --help     display this help and exit
  -p, --ports    specify number of ports
  -n, --name     specify module name
  -o, --output   specify output file name
"""

import io
import sys
import getopt
from math import *
from jinja2 import Template

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "?n:p:o:", ["help", "name=", "ports=", "output="])
        except getopt.error as msg:
             raise Usage(msg)
        # more code, unchanged  
    except Usage as err:
        print(err.msg, file=sys.stderr)
        print("for help use --help", file=sys.stderr)
        return 2
    
    ports = 2
    name = None
    out_name = None
    
    # process options
    for o, a in opts:
        if o in ('-?', '--help'):
            print(__doc__)
            sys.exit(0)
        if o in ('-p', '--ports'):
            ports = int(a)
        if o in ('-n', '--name'):
            name = a
        if o in ('-o', '--output'):
            out_name = a
    
    if name is None:
        name = "wb_mux_{0}".format(ports)
    
    if out_name is None:
        out_name = name + ".v"
    
    print("Opening file '%s'..." % out_name)
    
    try:
        out_file = open(out_name, 'w')
    except Exception as ex:
        print("Error opening \"%s\": %s" %(out_name, ex.strerror), file=sys.stderr)
        exit(1)
    
    print("Generating {0} port Wishbone mux {1}...".format(ports, name))
    
    select_width = ceil(log2(ports))
    
    t = Template(u"""/*

Copyright (c) 2015 Alex Forencich

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
    parameter DATA_WIDTH = 32,                  // width of data bus in bits (8, 16, 32, or 64)
    parameter ADDR_WIDTH = 32,                  // width of address bus in bits
    parameter SELECT_WIDTH = (DATA_WIDTH/8)     // width of word select bus (1, 2, 4, or 8)
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
    
    out_file.write(t.render(
        n=ports,
        w=select_width,
        name=name,
        ports=range(ports)
    ))
    
    print("Done")

if __name__ == "__main__":
    sys.exit(main())

