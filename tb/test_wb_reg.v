/*

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

`timescale 1ns / 1ps

/*
 * Testbench for wb_reg
 */
module test_wb_reg;

// Parameters
parameter DATA_WIDTH = 32;
parameter ADDR_WIDTH = 32;
parameter SELECT_WIDTH = 4;

// Inputs
reg clk = 0;
reg rst = 0;
reg [7:0] current_test = 0;

reg [ADDR_WIDTH-1:0] m_adr_i = 0;
reg [DATA_WIDTH-1:0] m_dat_i = 0;
reg m_we_i = 0;
reg [SELECT_WIDTH-1:0] m_sel_i = 0;
reg m_stb_i = 0;
reg m_cyc_i = 0;
reg [DATA_WIDTH-1:0] s_dat_i = 0;
reg s_ack_i = 0;
reg s_err_i = 0;
reg s_rty_i = 0;

// Outputs
wire [DATA_WIDTH-1:0] m_dat_o;
wire m_ack_o;
wire m_err_o;
wire m_rty_o;
wire [ADDR_WIDTH-1:0] s_adr_o;
wire [DATA_WIDTH-1:0] s_dat_o;
wire s_we_o;
wire [SELECT_WIDTH-1:0] s_sel_o;
wire s_stb_o;
wire s_cyc_o;

initial begin
    // myhdl integration
    $from_myhdl(clk,
                rst,
                current_test,
                m_adr_i,
                m_dat_i,
                m_we_i,
                m_sel_i,
                m_stb_i,
                m_cyc_i,
                s_dat_i,
                s_ack_i,
                s_err_i,
                s_rty_i);
    $to_myhdl(m_dat_o,
              m_ack_o,
              m_err_o,
              m_rty_o,
              s_adr_o,
              s_dat_o,
              s_we_o,
              s_sel_o,
              s_stb_o,
              s_cyc_o);

    // dump file
    $dumpfile("test_wb_reg.lxt");
    $dumpvars(0, test_wb_reg);
end

wb_reg #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH),
    .SELECT_WIDTH(SELECT_WIDTH)
)
UUT (
    .clk(clk),
    .rst(rst),
    .m_adr_i(m_adr_i),
    .m_dat_i(m_dat_i),
    .m_dat_o(m_dat_o),
    .m_we_i(m_we_i),
    .m_sel_i(m_sel_i),
    .m_stb_i(m_stb_i),
    .m_ack_o(m_ack_o),
    .m_err_o(m_err_o),
    .m_rty_o(m_rty_o),
    .m_cyc_i(m_cyc_i),
    .s_adr_o(s_adr_o),
    .s_dat_i(s_dat_i),
    .s_dat_o(s_dat_o),
    .s_we_o(s_we_o),
    .s_sel_o(s_sel_o),
    .s_stb_o(s_stb_o),
    .s_ack_i(s_ack_i),
    .s_err_i(s_err_i),
    .s_rty_i(s_rty_i),
    .s_cyc_o(s_cyc_o)
);

endmodule
