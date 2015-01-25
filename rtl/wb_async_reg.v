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
 * Wishbone register
 */
module wb_async_reg #
(
    parameter DATA_WIDTH = 32,  // width of data bus in bits (8, 16, 32, or 64)
    parameter ADDR_WIDTH = 32,  // width of address bus in bits
    parameter SELECT_WIDTH = 4  // width of word select bus (1, 2, 4, or 8)
)
(
    // master side
    input  wire                    m_clk,
    input  wire                    m_rst,
    input  wire [ADDR_WIDTH-1:0]   m_adr_i,   // ADR_I() address
    input  wire [DATA_WIDTH-1:0]   m_dat_i,   // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   m_dat_o,   // DAT_O() data out
    input  wire                    m_we_i,    // WE_I write enable input
    input  wire [SELECT_WIDTH-1:0] m_sel_i,   // SEL_I() select input
    input  wire                    m_stb_i,   // STB_I strobe input
    output wire                    m_ack_o,   // ACK_O acknowledge output
    output wire                    m_err_o,   // ERR_O error output
    output wire                    m_rty_o,   // RTY_O retry output
    input  wire                    m_cyc_i,   // CYC_I cycle input

    // slave side
    input  wire                    s_clk,
    input  wire                    s_rst,
    output wire [ADDR_WIDTH-1:0]   s_adr_o,   // ADR_O() address
    input  wire [DATA_WIDTH-1:0]   s_dat_i,   // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   s_dat_o,   // DAT_O() data out
    output wire                    s_we_o,    // WE_O write enable output
    output wire [SELECT_WIDTH-1:0] s_sel_o,   // SEL_O() select output
    output wire                    s_stb_o,   // STB_O strobe output
    input  wire                    s_ack_i,   // ACK_I acknowledge input
    input  wire                    s_err_i,   // ERR_I error input
    input  wire                    s_rty_i,   // RTY_I retry input
    output wire                    s_cyc_o    // CYC_O cycle output
);

reg [ADDR_WIDTH-1:0] m_adr_i_reg = 0;
reg [DATA_WIDTH-1:0] m_dat_i_reg = 0;
reg [DATA_WIDTH-1:0] m_dat_o_reg = 0;
reg m_we_i_reg = 0;
reg [SELECT_WIDTH-1:0] m_sel_i_reg = 0;
reg m_stb_i_reg = 0;
reg m_ack_o_reg = 0;
reg m_err_o_reg = 0;
reg m_rty_o_reg = 0;
reg m_cyc_i_reg = 0;

reg m_done_sync1 = 0;
reg m_done_sync2 = 0;
reg m_done_sync3 = 0;

reg [ADDR_WIDTH-1:0] s_adr_o_reg = 0;
reg [DATA_WIDTH-1:0] s_dat_i_reg = 0;
reg [DATA_WIDTH-1:0] s_dat_o_reg = 0;
reg s_we_o_reg = 0;
reg [SELECT_WIDTH-1:0] s_sel_o_reg = 0;
reg s_stb_o_reg = 0;
reg s_ack_i_reg = 0;
reg s_err_i_reg = 0;
reg s_rty_i_reg = 0;
reg s_cyc_o_reg = 0;

reg s_cyc_o_sync1 = 0;
reg s_cyc_o_sync2 = 0;
reg s_cyc_o_sync3 = 0;

reg s_stb_o_sync1 = 0;
reg s_stb_o_sync2 = 0;
reg s_stb_o_sync3 = 0;

reg s_done_reg = 0;

assign m_dat_o = m_dat_o_reg;
assign m_ack_o = m_ack_o_reg;
assign m_err_o = m_err_o_reg;
assign m_rty_o = m_rty_o_reg;

assign s_adr_o = s_adr_o_reg;
assign s_dat_o = s_dat_o_reg;
assign s_we_o = s_we_o_reg;
assign s_sel_o = s_sel_o_reg;
assign s_stb_o = s_stb_o_reg;
assign s_cyc_o = s_cyc_o_reg;

// master side logic
always @(posedge m_clk) begin
    if (m_rst) begin
        m_adr_i_reg <= 0;
        m_dat_i_reg <= 0;
        m_dat_o_reg <= 0;
        m_we_i_reg <= 0;
        m_sel_i_reg <= 0;
        m_stb_i_reg <= 0;
        m_ack_o_reg <= 0;
        m_err_o_reg <= 0;
        m_rty_o_reg <= 0;
        m_cyc_i_reg <= 0;
    end else begin
        if (m_cyc_i_reg & m_stb_i_reg) begin
            // cycle - hold master
            if (m_done_sync2 & ~m_done_sync3) begin
                // end of cycle - store slave
                m_dat_o_reg <= s_dat_i_reg;
                m_ack_o_reg <= s_ack_i_reg;
                m_err_o_reg <= s_err_i_reg;
                m_rty_o_reg <= s_rty_i_reg;
                m_we_i_reg <= 0;
                m_stb_i_reg <= 0;
            end
        end else begin
            // idle - store master
            m_adr_i_reg <= m_adr_i;
            m_dat_i_reg <= m_dat_i;
            m_dat_o_reg <= 0;
            m_we_i_reg <= m_we_i & ~(m_ack_o | m_err_o | m_rty_o);
            m_sel_i_reg <= m_sel_i;
            m_stb_i_reg <= m_stb_i & ~(m_ack_o | m_err_o | m_rty_o);
            m_ack_o_reg <= 0;
            m_err_o_reg <= 0;
            m_rty_o_reg <= 0;
            m_cyc_i_reg <= m_cyc_i;
        end
    end

    // synchronize signals
    m_done_sync1 <= s_done_reg;
    m_done_sync2 <= m_done_sync1;
    m_done_sync3 <= m_done_sync2;
end

// slave side logic
always @(posedge s_clk) begin
    if (s_rst) begin
        s_adr_o_reg <= 0;
        s_dat_i_reg <= 0;
        s_dat_o_reg <= 0;
        s_we_o_reg <= 0;
        s_sel_o_reg <= 0;
        s_stb_o_reg <= 0;
        s_ack_i_reg <= 0;
        s_err_i_reg <= 0;
        s_rty_i_reg <= 0;
        s_cyc_o_reg <= 0;
        s_done_reg <= 0;
    end else begin
        if (s_ack_i | s_err_i | s_rty_i) begin
            // end of cycle - store slave
            s_dat_i_reg <= s_dat_i;
            s_ack_i_reg <= s_ack_i;
            s_err_i_reg <= s_err_i;
            s_rty_i_reg <= s_rty_i;
            s_we_o_reg <= 0;
            s_stb_o_reg <= 0;
            s_done_reg <= 1;
        end else if (s_stb_o_sync2 & ~s_stb_o_sync3) begin
            // beginning of cycle - store master 
            s_adr_o_reg <= m_adr_i_reg;
            s_dat_i_reg <= 0;
            s_dat_o_reg <= m_dat_i_reg;
            s_we_o_reg <= m_we_i_reg;
            s_sel_o_reg <= m_sel_i_reg;
            s_stb_o_reg <= m_stb_i_reg;
            s_ack_i_reg <= 0;
            s_err_i_reg <= 0;
            s_rty_i_reg <= 0;
            s_cyc_o_reg <= m_cyc_i_reg;
            s_done_reg <= 0;
        end else if (~s_cyc_o_sync2 & s_cyc_o_sync3) begin
            // cyc deassert
            s_adr_o_reg <= 0;
            s_dat_i_reg <= 0;
            s_dat_o_reg <= 0;
            s_we_o_reg <= 0;
            s_sel_o_reg <= 0;
            s_stb_o_reg <= 0;
            s_ack_i_reg <= 0;
            s_err_i_reg <= 0;
            s_rty_i_reg <= 0;
            s_cyc_o_reg <= 0;
            s_done_reg <= 0;
        end
    end

    // synchronize signals
    s_cyc_o_sync1 <= m_cyc_i_reg;
    s_cyc_o_sync2 <= s_cyc_o_sync1;
    s_cyc_o_sync3 <= s_cyc_o_sync2;

    s_stb_o_sync1 <= m_stb_i_reg;
    s_stb_o_sync2 <= s_stb_o_sync1;
    s_stb_o_sync3 <= s_stb_o_sync2;
end

endmodule
