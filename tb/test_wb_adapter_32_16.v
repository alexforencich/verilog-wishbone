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

`timescale 1ns / 1ps

/*
 * Testbench for wb_adapter
 */
module test_wb_adapter_32_16;

// Parameters
parameter ADDR_WIDTH = 32;
parameter WBM_DATA_WIDTH = 32;
parameter WBM_SELECT_WIDTH = 4;
parameter WBS_DATA_WIDTH = 16;
parameter WBS_SELECT_WIDTH = 2;

// Inputs
reg clk = 0;
reg rst = 0;
reg [7:0] current_test = 0;

reg [ADDR_WIDTH-1:0] wbm_adr_i = 0;
reg [WBM_DATA_WIDTH-1:0] wbm_dat_i = 0;
reg wbm_we_i = 0;
reg [WBM_SELECT_WIDTH-1:0] wbm_sel_i = 0;
reg wbm_stb_i = 0;
reg wbm_cyc_i = 0;
reg [WBS_DATA_WIDTH-1:0] wbs_dat_i = 0;
reg wbs_ack_i = 0;
reg wbs_err_i = 0;
reg wbs_rty_i = 0;

// Outputs
wire [WBM_DATA_WIDTH-1:0] wbm_dat_o;
wire wbm_ack_o;
wire wbm_err_o;
wire wbm_rty_o;
wire [ADDR_WIDTH-1:0] wbs_adr_o;
wire [WBS_DATA_WIDTH-1:0] wbs_dat_o;
wire wbs_we_o;
wire [WBS_SELECT_WIDTH-1:0] wbs_sel_o;
wire wbs_stb_o;
wire wbs_cyc_o;

initial begin
    // myhdl integration
    $from_myhdl(
        clk,
        rst,
        current_test,
        wbm_adr_i,
        wbm_dat_i,
        wbm_we_i,
        wbm_sel_i,
        wbm_stb_i,
        wbm_cyc_i,
        wbs_dat_i,
        wbs_ack_i,
        wbs_err_i,
        wbs_rty_i
    );
    $to_myhdl(
        wbm_dat_o,
        wbm_ack_o,
        wbm_err_o,
        wbm_rty_o,
        wbs_adr_o,
        wbs_dat_o,
        wbs_we_o,
        wbs_sel_o,
        wbs_stb_o,
        wbs_cyc_o
    );

    // dump file
    $dumpfile("test_wb_adapter_32_16.lxt");
    $dumpvars(0, test_wb_adapter_32_16);
end

wb_adapter #(
    .ADDR_WIDTH(ADDR_WIDTH),
    .WBM_DATA_WIDTH(WBM_DATA_WIDTH),
    .WBM_SELECT_WIDTH(WBM_SELECT_WIDTH),
    .WBS_DATA_WIDTH(WBS_DATA_WIDTH),
    .WBS_SELECT_WIDTH(WBS_SELECT_WIDTH)
)
UUT (
    .clk(clk),
    .rst(rst),
    .wbm_adr_i(wbm_adr_i),
    .wbm_dat_i(wbm_dat_i),
    .wbm_dat_o(wbm_dat_o),
    .wbm_we_i(wbm_we_i),
    .wbm_sel_i(wbm_sel_i),
    .wbm_stb_i(wbm_stb_i),
    .wbm_ack_o(wbm_ack_o),
    .wbm_err_o(wbm_err_o),
    .wbm_rty_o(wbm_rty_o),
    .wbm_cyc_i(wbm_cyc_i),
    .wbs_adr_o(wbs_adr_o),
    .wbs_dat_i(wbs_dat_i),
    .wbs_dat_o(wbs_dat_o),
    .wbs_we_o(wbs_we_o),
    .wbs_sel_o(wbs_sel_o),
    .wbs_stb_o(wbs_stb_o),
    .wbs_ack_i(wbs_ack_i),
    .wbs_err_i(wbs_err_i),
    .wbs_rty_i(wbs_rty_i),
    .wbs_cyc_o(wbs_cyc_o)
);

endmodule
