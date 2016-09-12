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
 * Testbench for wb_dp_ram
 */
module test_wb_dp_ram;

// Parameters
parameter DATA_WIDTH = 32;
parameter ADDR_WIDTH = 16;
parameter SELECT_WIDTH = 4;

// Inputs
reg a_clk = 0;
reg a_rst = 0;
reg b_clk = 0;
reg b_rst = 0;
reg [7:0] current_test = 0;

reg [ADDR_WIDTH-1:0] a_adr_i = 0;
reg [DATA_WIDTH-1:0] a_dat_i = 0;
reg a_we_i = 0;
reg [SELECT_WIDTH-1:0] a_sel_i = 0;
reg a_stb_i = 0;
reg a_cyc_i = 0;
reg [ADDR_WIDTH-1:0] b_adr_i = 0;
reg [DATA_WIDTH-1:0] b_dat_i = 0;
reg b_we_i = 0;
reg [SELECT_WIDTH-1:0] b_sel_i = 0;
reg b_stb_i = 0;
reg b_cyc_i = 0;

// Outputs
wire [DATA_WIDTH-1:0] a_dat_o;
wire a_ack_o;
wire [DATA_WIDTH-1:0] b_dat_o;
wire b_ack_o;

initial begin
    // myhdl integration
    $from_myhdl(
        a_clk,
        a_rst,
        b_clk,
        b_rst,
        current_test,
        a_adr_i,
        a_dat_i,
        a_we_i,
        a_sel_i,
        a_stb_i,
        a_cyc_i,
        b_adr_i,
        b_dat_i,
        b_we_i,
        b_sel_i,
        b_stb_i,
        b_cyc_i
    );
    $to_myhdl(
        a_dat_o,
        a_ack_o,
        b_dat_o,
        b_ack_o
    );

    // dump file
    $dumpfile("test_wb_dp_ram.lxt");
    $dumpvars(0, test_wb_dp_ram);
end

wb_dp_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH),
    .SELECT_WIDTH(SELECT_WIDTH)
)
UUT (
    .a_clk(a_clk),
    .a_adr_i(a_adr_i),
    .a_dat_i(a_dat_i),
    .a_dat_o(a_dat_o),
    .a_we_i(a_we_i),
    .a_sel_i(a_sel_i),
    .a_stb_i(a_stb_i),
    .a_ack_o(a_ack_o),
    .a_cyc_i(a_cyc_i),
    .b_clk(b_clk),
    .b_adr_i(b_adr_i),
    .b_dat_i(b_dat_i),
    .b_dat_o(b_dat_o),
    .b_we_i(b_we_i),
    .b_sel_i(b_sel_i),
    .b_stb_i(b_stb_i),
    .b_ack_o(b_ack_o),
    .b_cyc_i(b_cyc_i)
);

endmodule
