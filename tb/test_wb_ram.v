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
 * Testbench for wb_ram
 */
module test_wb_ram;

// Parameters
parameter DATA_WIDTH = 32;
parameter ADDR_WIDTH = 16;
parameter SELECT_WIDTH = 4;

// Inputs
reg clk = 0;
reg rst = 0;
reg [7:0] current_test = 0;

reg [ADDR_WIDTH-1:0] adr_i = 0;
reg [DATA_WIDTH-1:0] dat_i = 0;
reg we_i = 0;
reg [SELECT_WIDTH-1:0] sel_i = 0;
reg stb_i = 0;
reg cyc_i = 0;

// Outputs
wire [DATA_WIDTH-1:0] dat_o;
wire ack_o;

initial begin
    // myhdl integration
    $from_myhdl(
        clk,
        rst,
        current_test,
        adr_i,
        dat_i,
        we_i,
        sel_i,
        stb_i,
        cyc_i
    );
    $to_myhdl(
        dat_o,
        ack_o
    );

    // dump file
    $dumpfile("test_wb_ram.lxt");
    $dumpvars(0, test_wb_ram);
end

wb_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH),
    .SELECT_WIDTH(SELECT_WIDTH)
)
UUT (
    .clk(clk),
    .adr_i(adr_i),
    .dat_i(dat_i),
    .dat_o(dat_o),
    .we_i(we_i),
    .sel_i(sel_i),
    .stb_i(stb_i),
    .ack_o(ack_o),
    .cyc_i(cyc_i)
);

endmodule
