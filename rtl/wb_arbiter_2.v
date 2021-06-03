/*

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
 * Wishbone 2 port arbiter
 */
module wb_arbiter_2 #
(
    parameter DATA_WIDTH = 32,                    // width of data bus in bits (8, 16, 32, or 64)
    parameter ADDR_WIDTH = 32,                    // width of address bus in bits
    parameter SELECT_WIDTH = (DATA_WIDTH/8),      // width of word select bus (1, 2, 4, or 8)
    parameter ARB_TYPE_ROUND_ROBIN = 0,           // select round robin arbitration
    parameter ARB_LSB_HIGH_PRIORITY = 1           // LSB priority selection
)
(
    input  wire                    clk,
    input  wire                    rst,

    /*
     * Wishbone master 0 input
     */
    input  wire [ADDR_WIDTH-1:0]   wbm0_adr_i,    // ADR_I() address input
    input  wire [DATA_WIDTH-1:0]   wbm0_dat_i,    // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbm0_dat_o,    // DAT_O() data out
    input  wire                    wbm0_we_i,     // WE_I write enable input
    input  wire [SELECT_WIDTH-1:0] wbm0_sel_i,    // SEL_I() select input
    input  wire                    wbm0_stb_i,    // STB_I strobe input
    output wire                    wbm0_ack_o,    // ACK_O acknowledge output
    output wire                    wbm0_err_o,    // ERR_O error output
    output wire                    wbm0_rty_o,    // RTY_O retry output
    input  wire                    wbm0_cyc_i,    // CYC_I cycle input

    /*
     * Wishbone master 1 input
     */
    input  wire [ADDR_WIDTH-1:0]   wbm1_adr_i,    // ADR_I() address input
    input  wire [DATA_WIDTH-1:0]   wbm1_dat_i,    // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbm1_dat_o,    // DAT_O() data out
    input  wire                    wbm1_we_i,     // WE_I write enable input
    input  wire [SELECT_WIDTH-1:0] wbm1_sel_i,    // SEL_I() select input
    input  wire                    wbm1_stb_i,    // STB_I strobe input
    output wire                    wbm1_ack_o,    // ACK_O acknowledge output
    output wire                    wbm1_err_o,    // ERR_O error output
    output wire                    wbm1_rty_o,    // RTY_O retry output
    input  wire                    wbm1_cyc_i,    // CYC_I cycle input

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

wire [1:0] request;
wire [1:0] grant;

assign request[0] = wbm0_cyc_i;
assign request[1] = wbm1_cyc_i;

wire wbm0_sel = grant[0] & grant_valid;
wire wbm1_sel = grant[1] & grant_valid;

// master 0
assign wbm0_dat_o = wbs_dat_i;
assign wbm0_ack_o = wbs_ack_i & wbm0_sel;
assign wbm0_err_o = wbs_err_i & wbm0_sel;
assign wbm0_rty_o = wbs_rty_i & wbm0_sel;

// master 1
assign wbm1_dat_o = wbs_dat_i;
assign wbm1_ack_o = wbs_ack_i & wbm1_sel;
assign wbm1_err_o = wbs_err_i & wbm1_sel;
assign wbm1_rty_o = wbs_rty_i & wbm1_sel;

// slave
assign wbs_adr_o = wbm0_sel ? wbm0_adr_i :
                   wbm1_sel ? wbm1_adr_i :
                   {ADDR_WIDTH{1'b0}};

assign wbs_dat_o = wbm0_sel ? wbm0_dat_i :
                   wbm1_sel ? wbm1_dat_i :
                   {DATA_WIDTH{1'b0}};

assign wbs_we_o = wbm0_sel ? wbm0_we_i :
                  wbm1_sel ? wbm1_we_i :
                  1'b0;

assign wbs_sel_o = wbm0_sel ? wbm0_sel_i :
                   wbm1_sel ? wbm1_sel_i :
                   {SELECT_WIDTH{1'b0}};

assign wbs_stb_o = wbm0_sel ? wbm0_stb_i :
                   wbm1_sel ? wbm1_stb_i :
                   1'b0;

assign wbs_cyc_o = wbm0_sel ? 1'b1 :
                   wbm1_sel ? 1'b1 :
                   1'b0;

// arbiter instance
arbiter #(
    .PORTS(2),
    .ARB_TYPE_ROUND_ROBIN(ARB_TYPE_ROUND_ROBIN),
    .ARB_BLOCK(1),
    .ARB_BLOCK_ACK(0),
    .ARB_LSB_HIGH_PRIORITY(ARB_LSB_HIGH_PRIORITY)
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
