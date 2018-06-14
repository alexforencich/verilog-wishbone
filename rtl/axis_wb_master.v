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
 * AXI stream wishbone master
 */
module axis_wb_master #
(
    parameter IMPLICIT_FRAMING = 0,                  // implicit framing (ignore tlast, look for start)
    parameter COUNT_SIZE = 16,                       // size of word count register
    parameter AXIS_DATA_WIDTH = 8,                   // width of AXI data bus
    parameter AXIS_KEEP_WIDTH = (AXIS_DATA_WIDTH/8), // width of AXI bus tkeep signal
    parameter WB_DATA_WIDTH = 32,                    // width of data bus in bits (8, 16, 32, or 64)
    parameter WB_ADDR_WIDTH = 32,                    // width of address bus in bits
    parameter WB_SELECT_WIDTH = (WB_DATA_WIDTH/8),   // width of word select bus (1, 2, 4, or 8)
    parameter READ_REQ = 8'hA1,                      // read requst type
    parameter WRITE_REQ = 8'hA2,                     // write requst type
    parameter READ_RESP = 8'hA3,                     // read response type
    parameter WRITE_RESP = 8'hA4                     // write response type
)
(
    input  wire                       clk,
    input  wire                       rst,

    /*
     * AXI input
     */
    input  wire [AXIS_DATA_WIDTH-1:0] input_axis_tdata,
    input  wire [AXIS_KEEP_WIDTH-1:0] input_axis_tkeep,
    input  wire                       input_axis_tvalid,
    output wire                       input_axis_tready,
    input  wire                       input_axis_tlast,
    input  wire                       input_axis_tuser,

    /*
     * AXI output
     */
    output wire [AXIS_DATA_WIDTH-1:0] output_axis_tdata,
    output wire [AXIS_KEEP_WIDTH-1:0] output_axis_tkeep,
    output wire                       output_axis_tvalid,
    input  wire                       output_axis_tready,
    output wire                       output_axis_tlast,
    output wire                       output_axis_tuser,

    /*
     * Wishbone interface
     */
    output wire [WB_ADDR_WIDTH-1:0]   wb_adr_o,   // ADR_O() address
    input  wire [WB_DATA_WIDTH-1:0]   wb_dat_i,   // DAT_I() data in
    output wire [WB_DATA_WIDTH-1:0]   wb_dat_o,   // DAT_O() data out
    output wire                       wb_we_o,    // WE_O write enable output
    output wire [WB_SELECT_WIDTH-1:0] wb_sel_o,   // SEL_O() select output
    output wire                       wb_stb_o,   // STB_O strobe output
    input  wire                       wb_ack_i,   // ACK_I acknowledge input
    input  wire                       wb_err_i,   // ERR_I error input
    output wire                       wb_cyc_o,   // CYC_O cycle output

    /*
     * Status
     */
    output wire                       busy
);

// bus word width
localparam AXIS_DATA_WORD_SIZE = AXIS_DATA_WIDTH / AXIS_KEEP_WIDTH;

// for interfaces that are more than one word wide, disable address lines
parameter WB_VALID_ADDR_WIDTH = WB_ADDR_WIDTH - $clog2(WB_SELECT_WIDTH);
// width of data port in words (1, 2, 4, or 8)
parameter WB_WORD_WIDTH = WB_SELECT_WIDTH;
// size of words (8, 16, 32, or 64 bits)
parameter WB_WORD_SIZE = WB_DATA_WIDTH/WB_WORD_WIDTH;

parameter WORD_PART_ADDR_WIDTH = $clog2(WB_WORD_SIZE/AXIS_DATA_WORD_SIZE);

parameter ADDR_WIDTH_ADJ = WB_ADDR_WIDTH+WORD_PART_ADDR_WIDTH;

parameter COUNT_WORD_WIDTH = (COUNT_SIZE+AXIS_DATA_WORD_SIZE-1)/AXIS_DATA_WORD_SIZE;
parameter ADDR_WORD_WIDTH = (ADDR_WIDTH_ADJ+AXIS_DATA_WORD_SIZE-1)/AXIS_DATA_WORD_SIZE;

// bus width assertions
initial begin
    if (AXIS_KEEP_WIDTH * AXIS_DATA_WORD_SIZE != AXIS_DATA_WIDTH) begin
        $error("Error: AXI data width not evenly divisble");
        $finish;
    end

    if (WB_WORD_WIDTH * WB_WORD_SIZE != WB_DATA_WIDTH) begin
        $error("Error: WB data width not evenly divisble");
        $finish;
    end

    if (2**$clog2(WB_WORD_WIDTH) != WB_WORD_WIDTH) begin
        $error("Error: WB word width must be even power of two");
        $finish;
    end

    if (AXIS_DATA_WORD_SIZE*2**$clog2(WB_WORD_SIZE/AXIS_DATA_WORD_SIZE) != WB_WORD_SIZE) begin
        $error("Error: WB word size must be a power of two multiple of the AXI word size");
        $finish;
    end

    if (AXIS_KEEP_WIDTH > 1) begin
        $error("Error: currently, only single word AXI bus supported");
        $finish;
    end
end

localparam [2:0]
    STATE_IDLE = 3'd0,
    STATE_HEADER = 3'd1,
    STATE_READ_1 = 3'd2,
    STATE_READ_2 = 3'd3,
    STATE_WRITE_1 = 3'd4,
    STATE_WRITE_2 = 3'd5,
    STATE_WAIT_LAST = 3'd6;

reg [2:0] state_reg = STATE_IDLE, state_next;

reg [COUNT_SIZE-1:0] ptr_reg = {COUNT_SIZE{1'b0}}, ptr_next;
reg [7:0] count_reg = 8'd0, count_next;
reg last_cycle_reg = 1'b0;

reg [ADDR_WIDTH_ADJ-1:0] addr_reg = {ADDR_WIDTH_ADJ{1'b0}}, addr_next;
reg [WB_DATA_WIDTH-1:0] data_reg = {WB_DATA_WIDTH{1'b0}}, data_next;

reg input_axis_tready_reg = 1'b0, input_axis_tready_next;

reg wb_we_o_reg = 1'b0, wb_we_o_next;
reg [WB_SELECT_WIDTH-1:0] wb_sel_o_reg = {WB_SELECT_WIDTH{1'b0}}, wb_sel_o_next;
reg wb_stb_o_reg = 1'b0, wb_stb_o_next;
reg wb_cyc_o_reg = 1'b0, wb_cyc_o_next;

reg busy_reg = 1'b0;

// internal datapath
reg [AXIS_DATA_WIDTH-1:0] output_axis_tdata_int;
reg [AXIS_KEEP_WIDTH-1:0] output_axis_tkeep_int;
reg                       output_axis_tvalid_int;
reg                       output_axis_tready_int_reg = 1'b0;
reg                       output_axis_tlast_int;
reg                       output_axis_tuser_int;
wire                      output_axis_tready_int_early;

assign input_axis_tready = input_axis_tready_reg;

assign wb_adr_o = {addr_reg[ADDR_WIDTH_ADJ-1:ADDR_WIDTH_ADJ-WB_VALID_ADDR_WIDTH], {WB_ADDR_WIDTH-WB_VALID_ADDR_WIDTH{1'b0}}};
assign wb_dat_o = data_reg;
assign wb_we_o = wb_we_o_reg;
assign wb_sel_o = wb_sel_o_reg;
assign wb_stb_o = wb_stb_o_reg;
assign wb_cyc_o = wb_cyc_o_reg;

assign busy = busy_reg;

always @* begin
    state_next = STATE_IDLE;

    ptr_next = ptr_reg;
    count_next = count_reg;

    input_axis_tready_next = 1'b0;

    output_axis_tdata_int = {AXIS_DATA_WIDTH{1'b0}};
    output_axis_tkeep_int = {{AXIS_KEEP_WIDTH-1{1'b0}}, 1'b1};
    output_axis_tvalid_int = 1'b0;
    output_axis_tlast_int = 1'b0;
    output_axis_tuser_int = 1'b0;

    addr_next = addr_reg;
    data_next = data_reg;

    wb_we_o_next = wb_we_o_reg;
    wb_sel_o_next = wb_sel_o_reg;
    wb_stb_o_next = 1'b0;
    wb_cyc_o_next = 1'b0;

    case (state_reg)
        STATE_IDLE: begin
            // idle, wait for start indicator
            input_axis_tready_next = output_axis_tready_int_early;
            wb_we_o_next = 1'b0;

            if (input_axis_tready & input_axis_tvalid) begin
                if (!IMPLICIT_FRAMING & input_axis_tlast) begin
                    // last asserted, ignore cycle
                    state_next = STATE_IDLE;
                end else if (input_axis_tdata == READ_REQ) begin
                    // start of read
                    output_axis_tdata_int = READ_RESP;
                    output_axis_tvalid_int = 1'b1;
                    output_axis_tlast_int = 1'b0;
                    output_axis_tuser_int = 1'b0;
                    wb_we_o_next = 1'b0;
                    count_next = COUNT_WORD_WIDTH+ADDR_WORD_WIDTH-1;
                    state_next = STATE_HEADER;
                end else if (input_axis_tdata == WRITE_REQ) begin
                    // start of write
                    output_axis_tdata_int = WRITE_RESP;
                    output_axis_tvalid_int = 1'b1;
                    output_axis_tlast_int = 1'b0;
                    output_axis_tuser_int = 1'b0;
                    wb_we_o_next = 1'b1;
                    count_next = COUNT_WORD_WIDTH+ADDR_WORD_WIDTH-1;
                    state_next = STATE_HEADER;
                end else begin
                    // invalid start of packet
                    if (IMPLICIT_FRAMING) begin
                        // drop byte
                        state_next = STATE_IDLE;
                    end else begin
                        // drop packet
                        state_next = STATE_WAIT_LAST;
                    end
                end
            end else begin
                state_next = STATE_IDLE;
            end
        end
        STATE_HEADER: begin
            // store address and length
            input_axis_tready_next = output_axis_tready_int_early;

            if (input_axis_tready & input_axis_tvalid) begin
                // pass through
                output_axis_tdata_int = input_axis_tdata;
                output_axis_tvalid_int = 1'b1;
                output_axis_tlast_int = 1'b0;
                output_axis_tuser_int = 1'b0;
                // store pointers
                if (count_reg < COUNT_WORD_WIDTH) begin
                    ptr_next[AXIS_DATA_WORD_SIZE*count_reg +: AXIS_DATA_WORD_SIZE] = input_axis_tdata;
                end else begin
                    addr_next[AXIS_DATA_WORD_SIZE*(count_reg-COUNT_WORD_WIDTH) +: AXIS_DATA_WORD_SIZE] = input_axis_tdata;
                end
                count_next = count_reg - 1;
                if (count_reg == 0) begin
                    // end of header
                    // set initial word offset
                    if (WB_ADDR_WIDTH == WB_VALID_ADDR_WIDTH && WORD_PART_ADDR_WIDTH == 0) begin
                        count_next = 0;
                    end else begin
                        count_next = addr_reg[ADDR_WIDTH_ADJ-WB_VALID_ADDR_WIDTH-1:0];
                    end
                    wb_sel_o_next = {WB_SELECT_WIDTH{1'b0}};
                    data_next = {WB_DATA_WIDTH{1'b0}};
                    if (wb_we_o_reg) begin
                        // start writing
                        if (input_axis_tlast) begin
                            // end of frame in header
                            output_axis_tlast_int = 1'b1;
                            output_axis_tuser_int = 1'b1;
                            state_next = STATE_IDLE;
                        end else begin
                            output_axis_tlast_int = 1'b1;
                            state_next = STATE_WRITE_1;
                        end
                    end else begin
                        // start reading
                        if (IMPLICIT_FRAMING) begin
                            input_axis_tready_next = 1'b0;
                        end else begin
                            input_axis_tready_next = !(last_cycle_reg || (input_axis_tvalid & input_axis_tlast));
                        end
                        wb_cyc_o_next = 1'b1;
                        wb_stb_o_next = 1'b1;
                        wb_sel_o_next = {WB_SELECT_WIDTH{1'b1}};
                        state_next = STATE_READ_1;
                    end
                end else begin
                    if (IMPLICIT_FRAMING) begin
                        state_next = STATE_HEADER;
                    end else begin
                        if (input_axis_tlast) begin
                            // end of frame in header
                            output_axis_tlast_int = 1'b1;
                            output_axis_tuser_int = 1'b1;
                            state_next = STATE_IDLE;
                        end else begin
                            state_next = STATE_HEADER;
                        end
                    end
                end
            end else begin
                state_next = STATE_HEADER;
            end
        end
        STATE_READ_1: begin
            // wait for ack
            wb_cyc_o_next = 1'b1;
            wb_stb_o_next = 1'b1;

            // drop padding
            if (!IMPLICIT_FRAMING) begin
                input_axis_tready_next = !(last_cycle_reg || (input_axis_tvalid & input_axis_tlast));
            end

            if (wb_ack_i || wb_err_i) begin
                // read cycle complete, store result
                data_next = wb_dat_i;
                addr_next = addr_reg + (1 << (WB_ADDR_WIDTH-WB_VALID_ADDR_WIDTH+WORD_PART_ADDR_WIDTH));
                wb_cyc_o_next = 1'b0;
                wb_stb_o_next = 1'b0;
                wb_sel_o_next = {WB_SELECT_WIDTH{1'b0}};
                state_next = STATE_READ_2;
            end else begin
                state_next = STATE_READ_1;
            end
        end
        STATE_READ_2: begin
            // send data

            // drop padding
            if (!IMPLICIT_FRAMING) begin
                input_axis_tready_next = !(last_cycle_reg || (input_axis_tvalid & input_axis_tlast));
            end

            if (output_axis_tready_int_reg) begin
                // transfer word and update pointers
                output_axis_tdata_int = data_reg[AXIS_DATA_WORD_SIZE*count_reg +: AXIS_DATA_WORD_SIZE];
                output_axis_tvalid_int = 1'b1;
                output_axis_tlast_int = 1'b0;
                output_axis_tuser_int = 1'b0;
                count_next = count_reg + 1;
                ptr_next = ptr_reg - 1;
                if (ptr_reg == 1) begin
                    // last word of read
                    output_axis_tlast_int = 1'b1;
                    if (!IMPLICIT_FRAMING && !(last_cycle_reg || (input_axis_tvalid & input_axis_tlast))) begin
                        state_next = STATE_WAIT_LAST;
                    end else begin
                        input_axis_tready_next = output_axis_tready_int_early;
                        state_next = STATE_IDLE;
                    end
                end else if (count_reg == (WB_SELECT_WIDTH*WB_WORD_SIZE/AXIS_DATA_WORD_SIZE)-1) begin
                    // end of stored data word; read the next one
                    count_next = 0;
                    wb_cyc_o_next = 1'b1;
                    wb_stb_o_next = 1'b1;
                    wb_sel_o_next = {WB_SELECT_WIDTH{1'b1}};
                    state_next = STATE_READ_1;
                end else begin
                    state_next = STATE_READ_2;
                end
            end else begin
                state_next = STATE_READ_2;
            end
        end
        STATE_WRITE_1: begin
            // write data
            input_axis_tready_next = 1'b1;

            if (input_axis_tready & input_axis_tvalid) begin
                // store word
                data_next[AXIS_DATA_WORD_SIZE*count_reg +: AXIS_DATA_WORD_SIZE] = input_axis_tdata;
                count_next = count_reg + 1;
                ptr_next = ptr_reg - 1;
                wb_sel_o_next[count_reg >> ((WB_WORD_SIZE/AXIS_DATA_WORD_SIZE)-1)] = 1'b1;
                if (count_reg == (WB_SELECT_WIDTH*WB_WORD_SIZE/AXIS_DATA_WORD_SIZE)-1 || ptr_reg == 1) begin
                    // have full word or at end of block, start write operation
                    count_next = 0;
                    input_axis_tready_next = 1'b0;
                    wb_cyc_o_next = 1'b1;
                    wb_stb_o_next = 1'b1;
                    state_next = STATE_WRITE_2;
                end else begin
                    state_next = STATE_WRITE_1;
                end
            end else begin
                state_next = STATE_WRITE_1;
            end
        end
        STATE_WRITE_2: begin
            // wait for ack
            wb_cyc_o_next = 1'b1;
            wb_stb_o_next = 1'b1;

            if (wb_ack_i || wb_err_i) begin
                // end of write operation
                data_next = {WB_DATA_WIDTH{1'b0}};
                addr_next = addr_reg + (1 << (WB_ADDR_WIDTH-WB_VALID_ADDR_WIDTH+WORD_PART_ADDR_WIDTH));
                wb_cyc_o_next = 1'b0;
                wb_stb_o_next = 1'b0;
                wb_sel_o_next = {WB_SELECT_WIDTH{1'b0}};
                if (ptr_reg == 0) begin
                    // done writing
                    if (!IMPLICIT_FRAMING && !last_cycle_reg) begin
                        input_axis_tready_next = 1'b1;
                        state_next = STATE_WAIT_LAST;
                    end else begin
                        input_axis_tready_next = output_axis_tready_int_early;
                        state_next = STATE_IDLE;
                    end
                end else begin
                    // more to write
                    state_next = STATE_WRITE_1;
                end
            end else begin
                state_next = STATE_WRITE_2;
            end
        end
        STATE_WAIT_LAST: begin
            // wait for end of frame
            input_axis_tready_next = 1'b1;

            if (input_axis_tready & input_axis_tvalid) begin
                // wait for tlast
                if (input_axis_tlast) begin
                    input_axis_tready_next = output_axis_tready_int_early;
                    state_next = STATE_IDLE;
                end else begin
                    state_next = STATE_WAIT_LAST;
                end
            end else begin
                state_next = STATE_WAIT_LAST;
            end
        end
    endcase
end

always @(posedge clk) begin
    if (rst) begin
        state_reg <= STATE_IDLE;
        input_axis_tready_reg <= 1'b0;
        wb_stb_o_reg <= 1'b0;
        wb_cyc_o_reg <= 1'b0;
        busy_reg <= 1'b0;
    end else begin
        state_reg <= state_next;
        input_axis_tready_reg <= input_axis_tready_next;
        wb_stb_o_reg <= wb_stb_o_next;
        wb_cyc_o_reg <= wb_cyc_o_next;
        busy_reg <= state_next != STATE_IDLE;
    end

    ptr_reg <= ptr_next;
    count_reg <= count_next;

    if (input_axis_tready & input_axis_tvalid) begin
        last_cycle_reg <= input_axis_tlast;
    end

    addr_reg <= addr_next;
    data_reg <= data_next;

    wb_we_o_reg <= wb_we_o_next;
    wb_sel_o_reg <= wb_sel_o_next;
end

// output datapath logic
reg [AXIS_DATA_WIDTH-1:0] output_axis_tdata_reg = {AXIS_DATA_WIDTH{1'b0}};
reg [AXIS_KEEP_WIDTH-1:0] output_axis_tkeep_reg = {{AXIS_KEEP_WIDTH-1{1'b0}}, 1'b1};
reg                       output_axis_tvalid_reg = 1'b0, output_axis_tvalid_next;
reg                       output_axis_tlast_reg = 1'b0;
reg                       output_axis_tuser_reg = 1'b0;

reg [AXIS_DATA_WIDTH-1:0] temp_axis_tdata_reg = {AXIS_DATA_WIDTH{1'b0}};
reg [AXIS_KEEP_WIDTH-1:0] temp_axis_tkeep_reg = {{AXIS_KEEP_WIDTH-1{1'b0}}, 1'b1};
reg                       temp_axis_tvalid_reg = 1'b0, temp_axis_tvalid_next;
reg                       temp_axis_tlast_reg = 1'b0;
reg                       temp_axis_tuser_reg = 1'b0;

// datapath control
reg store_axis_int_to_output;
reg store_axis_int_to_temp;
reg store_axis_temp_to_output;

assign output_axis_tdata = output_axis_tdata_reg;
assign output_axis_tkeep = output_axis_tkeep_reg;
assign output_axis_tvalid = output_axis_tvalid_reg;
assign output_axis_tlast = output_axis_tlast_reg;
assign output_axis_tuser = output_axis_tuser_reg;

// enable ready input next cycle if output is ready or the temp reg will not be filled on the next cycle (output reg empty or no input)
assign output_axis_tready_int_early = output_axis_tready | (~temp_axis_tvalid_reg & (~output_axis_tvalid_reg | ~output_axis_tvalid_int));

always @* begin
    // transfer sink ready state to source
    output_axis_tvalid_next = output_axis_tvalid_reg;
    temp_axis_tvalid_next = temp_axis_tvalid_reg;

    store_axis_int_to_output = 1'b0;
    store_axis_int_to_temp = 1'b0;
    store_axis_temp_to_output = 1'b0;
    
    if (output_axis_tready_int_reg) begin
        // input is ready
        if (output_axis_tready | ~output_axis_tvalid_reg) begin
            // output is ready or currently not valid, transfer data to output
            output_axis_tvalid_next = output_axis_tvalid_int;
            store_axis_int_to_output = 1'b1;
        end else begin
            // output is not ready, store input in temp
            temp_axis_tvalid_next = output_axis_tvalid_int;
            store_axis_int_to_temp = 1'b1;
        end
    end else if (output_axis_tready) begin
        // input is not ready, but output is ready
        output_axis_tvalid_next = temp_axis_tvalid_reg;
        temp_axis_tvalid_next = 1'b0;
        store_axis_temp_to_output = 1'b1;
    end
end

always @(posedge clk) begin
    if (rst) begin
        output_axis_tvalid_reg <= 1'b0;
        output_axis_tready_int_reg <= 1'b0;
        temp_axis_tvalid_reg <= 1'b0;
    end else begin
        output_axis_tvalid_reg <= output_axis_tvalid_next;
        output_axis_tready_int_reg <= output_axis_tready_int_early;
        temp_axis_tvalid_reg <= temp_axis_tvalid_next;
    end

    // datapath
    if (store_axis_int_to_output) begin
        output_axis_tdata_reg <= output_axis_tdata_int;
        output_axis_tkeep_reg <= output_axis_tkeep_int;
        output_axis_tlast_reg <= output_axis_tlast_int;
        output_axis_tuser_reg <= output_axis_tuser_int;
    end else if (store_axis_temp_to_output) begin
        output_axis_tdata_reg <= temp_axis_tdata_reg;
        output_axis_tkeep_reg <= temp_axis_tkeep_reg;
        output_axis_tlast_reg <= temp_axis_tlast_reg;
        output_axis_tuser_reg <= temp_axis_tuser_reg;
    end

    if (store_axis_int_to_temp) begin
        temp_axis_tdata_reg <= output_axis_tdata_int;
        temp_axis_tkeep_reg <= output_axis_tkeep_int;
        temp_axis_tlast_reg <= output_axis_tlast_int;
        temp_axis_tuser_reg <= output_axis_tuser_int;
    end
end

endmodule
