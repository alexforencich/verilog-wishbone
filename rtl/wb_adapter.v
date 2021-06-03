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
 * Wishbone width adapter
 */
module wb_adapter #
(
    parameter ADDR_WIDTH = 32,                        // width of address bus in bits
    parameter WBM_DATA_WIDTH = 32,                    // width of master data bus in bits (8, 16, 32, or 64)
    parameter WBM_SELECT_WIDTH = (WBM_DATA_WIDTH/8),  // width of master word select bus (1, 2, 4, or 8)
    parameter WBS_DATA_WIDTH = 32,                    // width of slave data bus in bits (8, 16, 32, or 64)
    parameter WBS_SELECT_WIDTH = (WBS_DATA_WIDTH/8)   // width of slave word select bus (1, 2, 4, or 8)
)
(
    input  wire                        clk,
    input  wire                        rst,

    /*
     * Wishbone master input
     */
    input  wire [ADDR_WIDTH-1:0]       wbm_adr_i,     // ADR_I() address input
    input  wire [WBM_DATA_WIDTH-1:0]   wbm_dat_i,     // DAT_I() data in
    output wire [WBM_DATA_WIDTH-1:0]   wbm_dat_o,     // DAT_O() data out
    input  wire                        wbm_we_i,      // WE_I write enable input
    input  wire [WBM_SELECT_WIDTH-1:0] wbm_sel_i,     // SEL_I() select input
    input  wire                        wbm_stb_i,     // STB_I strobe input
    output wire                        wbm_ack_o,     // ACK_O acknowledge output
    output wire                        wbm_err_o,     // ERR_O error output
    output wire                        wbm_rty_o,     // RTY_O retry output
    input  wire                        wbm_cyc_i,     // CYC_I cycle input

    /*
     * Wishbone slave output
     */
    output wire [ADDR_WIDTH-1:0]       wbs_adr_o,     // ADR_O() address output
    input  wire [WBS_DATA_WIDTH-1:0]   wbs_dat_i,     // DAT_I() data in
    output wire [WBS_DATA_WIDTH-1:0]   wbs_dat_o,     // DAT_O() data out
    output wire                        wbs_we_o,      // WE_O write enable output
    output wire [WBS_SELECT_WIDTH-1:0] wbs_sel_o,     // SEL_O() select output
    output wire                        wbs_stb_o,     // STB_O strobe output
    input  wire                        wbs_ack_i,     // ACK_I acknowledge input
    input  wire                        wbs_err_i,     // ERR_I error input
    input  wire                        wbs_rty_i,     // RTY_I retry input
    output wire                        wbs_cyc_o      // CYC_O cycle output
);

// address bit offets
parameter WBM_ADDR_BIT_OFFSET = $clog2(WBM_SELECT_WIDTH);
parameter WBS_ADDR_BIT_OFFSET = $clog2(WBS_SELECT_WIDTH);
// for interfaces that are more than one word wide, disable address lines
parameter WBM_VALID_ADDR_WIDTH = ADDR_WIDTH - WBM_ADDR_BIT_OFFSET;
parameter WBS_VALID_ADDR_WIDTH = ADDR_WIDTH - WBS_ADDR_BIT_OFFSET;
// width of data port in words (1, 2, 4, or 8)
parameter WBM_WORD_WIDTH = WBM_SELECT_WIDTH;
parameter WBS_WORD_WIDTH = WBS_SELECT_WIDTH;
// size of words (8, 16, 32, or 64 bits)
parameter WBM_WORD_SIZE = WBM_DATA_WIDTH/WBM_WORD_WIDTH;
parameter WBS_WORD_SIZE = WBS_DATA_WIDTH/WBS_WORD_WIDTH;
// required number of cycles to match widths
localparam CYCLE_COUNT = (WBM_SELECT_WIDTH > WBS_SELECT_WIDTH) ? (WBM_SELECT_WIDTH / WBS_SELECT_WIDTH) : (WBS_SELECT_WIDTH / WBM_SELECT_WIDTH);

// bus width assertions
initial begin
    if (WBM_WORD_WIDTH * WBM_WORD_SIZE != WBM_DATA_WIDTH) begin
        $error("Error: master data width not evenly divisble");
        $finish;
    end

    if (WBS_WORD_WIDTH * WBS_WORD_SIZE != WBS_DATA_WIDTH) begin
        $error("Error: slave data width not evenly divisble");
        $finish;
    end

    if (WBM_WORD_SIZE != WBS_WORD_SIZE) begin
        $error("Error: word size mismatch");
        $finish;
    end
end

// state register
localparam [1:0]
    STATE_IDLE = 2'd0,
    STATE_WAIT_ACK = 2'd1,
    STATE_PAUSE = 2'd2;

reg [1:0] state_reg = STATE_IDLE, state_next;

reg [CYCLE_COUNT-1:0] cycle_mask_reg = {CYCLE_COUNT{1'b1}}, cycle_mask_next;
reg [CYCLE_COUNT-1:0] cycle_sel_raw;
wire [CYCLE_COUNT-1:0] cycle_sel;
wire [$clog2(CYCLE_COUNT)-1:0] cycle_sel_enc;
wire cycle_sel_valid;

reg [$clog2(CYCLE_COUNT)-1:0] current_cycle_reg = 0, current_cycle_next;

reg [WBM_DATA_WIDTH-1:0] wbm_dat_o_reg = {WBM_DATA_WIDTH{1'b0}}, wbm_dat_o_next;
reg wbm_ack_o_reg = 1'b0, wbm_ack_o_next;
reg wbm_err_o_reg = 1'b0, wbm_err_o_next;
reg wbm_rty_o_reg = 1'b0, wbm_rty_o_next;

reg [ADDR_WIDTH-1:0] wbs_adr_o_reg = {ADDR_WIDTH{1'b0}}, wbs_adr_o_next;
reg [WBS_DATA_WIDTH-1:0] wbs_dat_o_reg = {WBS_DATA_WIDTH{1'b0}}, wbs_dat_o_next;
reg wbs_we_o_reg = 1'b0, wbs_we_o_next;
reg [WBS_SELECT_WIDTH-1:0] wbs_sel_o_reg = {WBS_SELECT_WIDTH{1'b0}}, wbs_sel_o_next;
reg wbs_stb_o_reg = 1'b0, wbs_stb_o_next;
reg wbs_cyc_o_reg = 1'b0, wbs_cyc_o_next;

assign wbm_dat_o = wbm_dat_o_reg;
assign wbm_ack_o = wbm_ack_o_reg;
assign wbm_err_o = wbm_err_o_reg;
assign wbm_rty_o = wbm_rty_o_reg;

assign wbs_adr_o = wbs_adr_o_reg;
assign wbs_dat_o = wbs_dat_o_reg;
assign wbs_we_o = wbs_we_o_reg;
assign wbs_sel_o = wbs_sel_o_reg;
assign wbs_stb_o = wbs_stb_o_reg;
assign wbs_cyc_o = wbs_cyc_o_reg;

priority_encoder #(
    .WIDTH(CYCLE_COUNT),
    .LSB_HIGH_PRIORITY(1)
)
cycle_encoder_inst (
    .input_unencoded(cycle_sel_raw & cycle_mask_reg),
    .output_valid(cycle_sel_valid),
    .output_encoded(cycle_sel_enc),
    .output_unencoded(cycle_sel)
);

integer j;

always @* begin
    for (j = 0; j < CYCLE_COUNT; j = j + 1) begin
        cycle_sel_raw[j] <= wbm_sel_i[j*WBS_SELECT_WIDTH +: WBS_SELECT_WIDTH] != 0;
    end
end

integer i;

always @* begin
    state_next = STATE_IDLE;

    cycle_mask_next = cycle_mask_reg;

    current_cycle_next = current_cycle_reg;

    wbm_dat_o_next = wbm_dat_o_reg;
    wbm_ack_o_next = 1'b0;
    wbm_err_o_next = 1'b0;
    wbm_rty_o_next = 1'b0;

    wbs_adr_o_next = wbs_adr_o_reg;
    wbs_dat_o_next = wbs_dat_o_reg;
    wbs_we_o_next = wbs_we_o_reg;
    wbs_sel_o_next = wbs_sel_o_reg;
    wbs_stb_o_next = wbs_stb_o_reg;
    wbs_cyc_o_next = wbs_cyc_o_reg;

    if (WBM_WORD_WIDTH > WBS_WORD_WIDTH) begin
        // master is wider (multiple cycles may be necessary)
        case (state_reg)
            STATE_IDLE: begin
                // idle state
                wbm_dat_o_next = 1'b0;
                wbs_cyc_o_next = wbm_cyc_i;

                cycle_mask_next = {CYCLE_COUNT{1'b1}};

                state_next = STATE_IDLE;

                if (wbm_cyc_i & wbm_stb_i & ~(wbm_ack_o | wbm_err_o | wbm_rty_o)) begin
                    // master cycle start
                    wbm_err_o_next = 1'b1;

                    if (cycle_sel_valid) begin
                        // set current cycle and mask for next cycle
                        current_cycle_next = cycle_sel_enc;
                        cycle_mask_next = {CYCLE_COUNT{1'b1}} << (cycle_sel_enc+1);
                        // mask address for slave alignment
                        wbs_adr_o_next = wbm_adr_i & ({ADDR_WIDTH{1'b1}} << WBM_ADDR_BIT_OFFSET);
                        wbs_adr_o_next[WBM_ADDR_BIT_OFFSET - 1:WBS_ADDR_BIT_OFFSET] = cycle_sel_enc;
                        // select corresponding data word
                        wbs_dat_o_next = wbm_dat_i[cycle_sel_enc*WBS_DATA_WIDTH +: WBS_DATA_WIDTH];
                        wbs_we_o_next = wbm_we_i;
                        // select proper select lines
                        wbs_sel_o_next = wbm_sel_i[cycle_sel_enc*WBS_SELECT_WIDTH +: WBS_SELECT_WIDTH];
                        wbs_stb_o_next = 1'b1;
                        wbs_cyc_o_next = 1'b1;
                        wbm_err_o_next = 1'b0;
                        state_next = STATE_WAIT_ACK;
                    end
                end
            end
            STATE_WAIT_ACK: begin
                if (wbs_err_i | wbs_rty_i) begin
                    // error or retry - stop and propagate condition to master
                    cycle_mask_next = {CYCLE_COUNT{1'b1}};
                    wbm_ack_o_next = wbs_ack_i;
                    wbm_err_o_next = wbs_err_i;
                    wbm_rty_o_next = wbs_rty_i;
                    wbs_we_o_next = 1'b0;
                    wbs_stb_o_next = 1'b0;
                    state_next = STATE_IDLE;
                end else if (wbs_ack_i) begin
                    // end of cycle - pass through slave to master
                    // store output word with proper offset
                    wbm_dat_o_next[current_cycle_reg*WBS_DATA_WIDTH +: WBS_DATA_WIDTH] = wbs_dat_i;
                    wbm_ack_o_next = wbs_ack_i;
                    wbs_we_o_next = 1'b0;
                    wbs_stb_o_next = 1'b0;

                    cycle_mask_next = {CYCLE_COUNT{1'b1}};
                    state_next = STATE_IDLE;

                    if (cycle_sel_valid) begin
                        // set current cycle and mask for next cycle
                        current_cycle_next = cycle_sel_enc;
                        cycle_mask_next = {CYCLE_COUNT{1'b1}} << (cycle_sel_enc+1);
                        // mask address for slave alignment
                        wbs_adr_o_next = wbm_adr_i & ({ADDR_WIDTH{1'b1}} << WBM_ADDR_BIT_OFFSET);
                        wbs_adr_o_next[WBM_ADDR_BIT_OFFSET - 1:WBS_ADDR_BIT_OFFSET] = cycle_sel_enc;
                        // select corresponding data word
                        wbs_dat_o_next = wbm_dat_i[cycle_sel_enc*WBS_DATA_WIDTH +: WBS_DATA_WIDTH];
                        wbs_we_o_next = wbm_we_i;
                        // select proper select lines
                        wbs_sel_o_next = wbm_sel_i[cycle_sel_enc*WBS_SELECT_WIDTH +: WBS_SELECT_WIDTH];
                        wbs_stb_o_next = 1'b0;
                        wbs_cyc_o_next = 1'b1;
                        wbm_ack_o_next = 1'b0;
                        state_next = STATE_PAUSE;
                    end
                end else begin
                    state_next = STATE_WAIT_ACK;
                end
            end
            STATE_PAUSE: begin
                // start new cycle
                wbs_stb_o_next = 1'b1;
                state_next = STATE_WAIT_ACK;
            end
        endcase
    end else if (WBS_WORD_WIDTH > WBM_WORD_WIDTH) begin
        // slave is wider (always single cycle)
        if (wbs_cyc_o_reg & wbs_stb_o_reg) begin
            // cycle - hold values
            if (wbs_ack_i | wbs_err_i | wbs_rty_i) begin
                // end of cycle - pass through slave to master
                // select output word based on address LSBs
                wbm_dat_o_next = wbs_dat_i >> (wbm_adr_i[WBS_ADDR_BIT_OFFSET - 1:WBM_ADDR_BIT_OFFSET] * WBM_DATA_WIDTH);
                wbm_ack_o_next = wbs_ack_i;
                wbm_err_o_next = wbs_err_i;
                wbm_rty_o_next = wbs_rty_i;
                wbs_we_o_next = 1'b0;
                wbs_stb_o_next = 1'b0;
            end
        end else begin
            // idle - pass through master to slave
            wbm_ack_o_next = 1'b0;
            wbm_err_o_next = 1'b0;
            wbm_rty_o_next = 1'b0;
            // mask address for slave alignment
            wbs_adr_o_next = wbm_adr_i & ({ADDR_WIDTH{1'b1}} << WBS_ADDR_BIT_OFFSET);
            // duplicate input data across output port
            wbs_dat_o_next = {(WBS_WORD_WIDTH / WBM_WORD_WIDTH){wbm_dat_i}};
            wbs_we_o_next = wbm_we_i & ~(wbm_ack_o | wbm_err_o | wbm_rty_o);
            // shift select lines based on address LSBs
            wbs_sel_o_next = wbm_sel_i << (wbm_adr_i[WBS_ADDR_BIT_OFFSET - 1:WBM_ADDR_BIT_OFFSET] * WBM_SELECT_WIDTH);
            wbs_stb_o_next = wbm_stb_i & ~(wbm_ack_o | wbm_err_o | wbm_rty_o);
            wbs_cyc_o_next = wbm_cyc_i;
        end
    end else begin
        // same width - act as a simple register
        if (wbs_cyc_o_reg & wbs_stb_o_reg) begin
            // cycle - hold values
            if (wbs_ack_i | wbs_err_i | wbs_rty_i) begin
                // end of cycle - pass through slave to master
                wbm_dat_o_next = wbs_dat_i;
                wbm_ack_o_next = wbs_ack_i;
                wbm_err_o_next = wbs_err_i;
                wbm_rty_o_next = wbs_rty_i;
                wbs_we_o_next = 1'b0;
                wbs_stb_o_next = 1'b0;
            end
        end else begin
            // idle - pass through master to slave
            wbm_ack_o_next = 1'b0;
            wbm_err_o_next = 1'b0;
            wbm_rty_o_next = 1'b0;
            wbs_adr_o_next = wbm_adr_i;
            wbs_dat_o_next = wbm_dat_i;
            wbs_we_o_next = wbm_we_i & ~(wbm_ack_o | wbm_err_o | wbm_rty_o);
            wbs_sel_o_next = wbm_sel_i;
            wbs_stb_o_next = wbm_stb_i & ~(wbm_ack_o | wbm_err_o | wbm_rty_o);
            wbs_cyc_o_next = wbm_cyc_i;
        end
    end
end

always @(posedge clk) begin
    if (rst) begin
        state_reg <= STATE_IDLE;

        cycle_mask_reg <= {CYCLE_COUNT{1'b1}};

        wbm_ack_o_reg <= 1'b0;
        wbm_err_o_reg <= 1'b0;
        wbm_rty_o_reg <= 1'b0;

        wbs_stb_o_reg <= 1'b0;
        wbs_cyc_o_reg <= 1'b0;
    end else begin
        state_reg <= state_next;

        cycle_mask_reg <= cycle_mask_next;

        wbm_ack_o_reg <= wbm_ack_o_next;
        wbm_err_o_reg <= wbm_err_o_next;
        wbm_rty_o_reg <= wbm_rty_o_next;

        wbs_stb_o_reg <= wbs_stb_o_next;
        wbs_cyc_o_reg <= wbs_cyc_o_next;
    end

    current_cycle_reg <= current_cycle_next;

    wbm_dat_o_reg <= wbm_dat_o_next;

    wbs_adr_o_reg <= wbs_adr_o_next;
    wbs_dat_o_reg <= wbs_dat_o_next;
    wbs_we_o_reg <= wbs_we_o_next;
    wbs_sel_o_reg <= wbs_sel_o_next;
end

endmodule
