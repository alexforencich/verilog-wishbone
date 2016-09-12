/*

Copyright (c) 2016 Alex Forencich

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
 * Testbench for axis_wb_master
 */
module test_axis_wb_master_8_32_imp;

// Parameters
parameter IMPLICIT_FRAMING = 1;
parameter COUNT_SIZE = 16;
parameter AXIS_DATA_WIDTH = 8;
parameter AXIS_KEEP_WIDTH = (AXIS_DATA_WIDTH/8);
parameter WB_DATA_WIDTH = 32;
parameter WB_ADDR_WIDTH = 32;
parameter WB_SELECT_WIDTH = (WB_DATA_WIDTH/8);
parameter READ_REQ = 8'hA1;
parameter WRITE_REQ = 8'hA2;
parameter READ_RESP = 8'hA3;
parameter WRITE_RESP = 8'hA4;

// Inputs
reg clk = 0;
reg rst = 0;
reg [7:0] current_test = 0;

reg [AXIS_DATA_WIDTH-1:0] input_axis_tdata = 0;
reg [AXIS_KEEP_WIDTH-1:0] input_axis_tkeep = 0;
reg input_axis_tvalid = 0;
reg input_axis_tlast = 0;
reg input_axis_tuser = 0;
reg output_axis_tready = 0;
reg [WB_DATA_WIDTH-1:0] wb_dat_i = 0;
reg wb_ack_i = 0;
reg wb_err_i = 0;

// Outputs
wire input_axis_tready;
wire [AXIS_DATA_WIDTH-1:0] output_axis_tdata;
wire [AXIS_KEEP_WIDTH-1:0] output_axis_tkeep;
wire output_axis_tvalid;
wire output_axis_tlast;
wire output_axis_tuser;
wire [WB_ADDR_WIDTH-1:0] wb_adr_o;
wire [WB_DATA_WIDTH-1:0] wb_dat_o;
wire wb_we_o;
wire [WB_SELECT_WIDTH-1:0] wb_sel_o;
wire wb_stb_o;
wire wb_cyc_o;
wire busy;

initial begin
    // myhdl integration
    $from_myhdl(
        clk,
        rst,
        current_test,
        input_axis_tdata,
        input_axis_tkeep,
        input_axis_tvalid,
        input_axis_tlast,
        input_axis_tuser,
        output_axis_tready,
        wb_dat_i,
        wb_ack_i,
        wb_err_i
    );
    $to_myhdl(
        input_axis_tready,
        output_axis_tdata,
        output_axis_tkeep,
        output_axis_tvalid,
        output_axis_tlast,
        output_axis_tuser,
        wb_adr_o,
        wb_dat_o,
        wb_we_o,
        wb_sel_o,
        wb_stb_o,
        wb_cyc_o,
        busy
    );

    // dump file
    $dumpfile("test_axis_wb_master_8_32_imp.lxt");
    $dumpvars(0, test_axis_wb_master_8_32_imp);
end

axis_wb_master #(
    .IMPLICIT_FRAMING(IMPLICIT_FRAMING),
    .COUNT_SIZE(COUNT_SIZE),
    .AXIS_DATA_WIDTH(AXIS_DATA_WIDTH),
    .AXIS_KEEP_WIDTH(AXIS_KEEP_WIDTH),
    .WB_DATA_WIDTH(WB_DATA_WIDTH),
    .WB_ADDR_WIDTH(WB_ADDR_WIDTH),
    .WB_SELECT_WIDTH(WB_SELECT_WIDTH),
    .READ_REQ(READ_REQ),
    .WRITE_REQ(WRITE_REQ),
    .READ_RESP(READ_RESP),
    .WRITE_RESP(WRITE_RESP)
)
UUT (
    .clk(clk),
    .rst(rst),
    .input_axis_tdata(input_axis_tdata),
    .input_axis_tkeep(input_axis_tkeep),
    .input_axis_tvalid(input_axis_tvalid),
    .input_axis_tready(input_axis_tready),
    .input_axis_tlast(input_axis_tlast),
    .input_axis_tuser(input_axis_tuser),
    .output_axis_tdata(output_axis_tdata),
    .output_axis_tkeep(output_axis_tkeep),
    .output_axis_tvalid(output_axis_tvalid),
    .output_axis_tready(output_axis_tready),
    .output_axis_tlast(output_axis_tlast),
    .output_axis_tuser(output_axis_tuser),
    .wb_adr_o(wb_adr_o),
    .wb_dat_i(wb_dat_i),
    .wb_dat_o(wb_dat_o),
    .wb_we_o(wb_we_o),
    .wb_sel_o(wb_sel_o),
    .wb_stb_o(wb_stb_o),
    .wb_ack_i(wb_ack_i),
    .wb_err_i(wb_err_i),
    .wb_cyc_o(wb_cyc_o),
    .busy(busy)
);

endmodule
