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
 * Wishbone 2 port multiplexer
 */
module wb_mux_2 #
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

    /*
     * Wishbone slave 0 output
     */
    output wire [ADDR_WIDTH-1:0]   wbs0_adr_o,    // ADR_O() address output
    input  wire [DATA_WIDTH-1:0]   wbs0_dat_i,    // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbs0_dat_o,    // DAT_O() data out
    output wire                    wbs0_we_o,     // WE_O write enable output
    output wire [SELECT_WIDTH-1:0] wbs0_sel_o,    // SEL_O() select output
    output wire                    wbs0_stb_o,    // STB_O strobe output
    input  wire                    wbs0_ack_i,    // ACK_I acknowledge input
    input  wire                    wbs0_err_i,    // ERR_I error input
    input  wire                    wbs0_rty_i,    // RTY_I retry input
    output wire                    wbs0_cyc_o,    // CYC_O cycle output

    /*
     * Wishbone slave 0 address configuration
     */
    input  wire [ADDR_WIDTH-1:0]   wbs0_addr,     // Slave address prefix
    input  wire [ADDR_WIDTH-1:0]   wbs0_addr_msk, // Slave address prefix mask

    /*
     * Wishbone slave 1 output
     */
    output wire [ADDR_WIDTH-1:0]   wbs1_adr_o,    // ADR_O() address output
    input  wire [DATA_WIDTH-1:0]   wbs1_dat_i,    // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbs1_dat_o,    // DAT_O() data out
    output wire                    wbs1_we_o,     // WE_O write enable output
    output wire [SELECT_WIDTH-1:0] wbs1_sel_o,    // SEL_O() select output
    output wire                    wbs1_stb_o,    // STB_O strobe output
    input  wire                    wbs1_ack_i,    // ACK_I acknowledge input
    input  wire                    wbs1_err_i,    // ERR_I error input
    input  wire                    wbs1_rty_i,    // RTY_I retry input
    output wire                    wbs1_cyc_o,    // CYC_O cycle output

    /*
     * Wishbone slave 1 address configuration
     */
    input  wire [ADDR_WIDTH-1:0]   wbs1_addr,     // Slave address prefix
    input  wire [ADDR_WIDTH-1:0]   wbs1_addr_msk  // Slave address prefix mask
);

wire wbs0_match = ~|((wbm_adr_i ^ wbs0_addr) & wbs0_addr_msk);
wire wbs1_match = ~|((wbm_adr_i ^ wbs1_addr) & wbs1_addr_msk);

wire wbs0_sel = wbs0_match;
wire wbs1_sel = wbs1_match & ~(wbs0_match);

wire master_cycle = wbm_cyc_i & wbm_stb_i;

wire select_error = ~(wbs0_sel | wbs1_sel) & master_cycle;

// master
assign wbm_dat_o = wbs0_sel ? wbs0_dat_i :
                   wbs1_sel ? wbs1_dat_i :
                   {DATA_WIDTH{1'b0}};

assign wbm_ack_o = wbs0_ack_i |
                   wbs1_ack_i;

assign wbm_err_o = wbs0_err_i |
                   wbs1_err_i |
                   select_error;

assign wbm_rty_o = wbs0_rty_i |
                   wbs1_rty_i;

// slave 0
assign wbs0_adr_o = wbm_adr_i;
assign wbs0_dat_o = wbm_dat_i;
assign wbs0_we_o = wbm_we_i & wbs0_sel;
assign wbs0_sel_o = wbm_sel_i;
assign wbs0_stb_o = wbm_stb_i & wbs0_sel;
assign wbs0_cyc_o = wbm_cyc_i & wbs0_sel;

// slave 1
assign wbs1_adr_o = wbm_adr_i;
assign wbs1_dat_o = wbm_dat_i;
assign wbs1_we_o = wbm_we_i & wbs1_sel;
assign wbs1_sel_o = wbm_sel_i;
assign wbs1_stb_o = wbm_stb_i & wbs1_sel;
assign wbs1_cyc_o = wbm_cyc_i & wbs1_sel;


endmodule
