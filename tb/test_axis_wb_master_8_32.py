#!/usr/bin/env python
"""

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

"""

from myhdl import *
import os
import struct

import axis_ep
import wb

module = 'axis_wb_master'
testbench = 'test_%s_8_32' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    IMPLICIT_FRAMING = 0
    COUNT_SIZE = 16
    AXIS_DATA_WIDTH = 8
    AXIS_KEEP_WIDTH = (AXIS_DATA_WIDTH/8)
    WB_DATA_WIDTH = 32
    WB_ADDR_WIDTH = 32
    WB_SELECT_WIDTH = (WB_DATA_WIDTH/8)
    READ_REQ = 0xA1
    WRITE_REQ = 0xA2
    READ_RESP = 0xA3
    WRITE_RESP = 0xA4

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    input_axis_tdata = Signal(intbv(0)[AXIS_DATA_WIDTH:])
    input_axis_tkeep = Signal(intbv(1)[AXIS_KEEP_WIDTH:])
    input_axis_tvalid = Signal(bool(0))
    input_axis_tlast = Signal(bool(0))
    input_axis_tuser = Signal(bool(0))
    output_axis_tready = Signal(bool(0))
    wb_dat_i = Signal(intbv(0)[WB_DATA_WIDTH:])
    wb_ack_i = Signal(bool(0))
    wb_err_i = Signal(bool(0))

    # Outputs
    input_axis_tready = Signal(bool(0))
    output_axis_tdata = Signal(intbv(0)[AXIS_DATA_WIDTH:])
    output_axis_tkeep = Signal(intbv(1)[AXIS_KEEP_WIDTH:])
    output_axis_tvalid = Signal(bool(0))
    output_axis_tlast = Signal(bool(0))
    output_axis_tuser = Signal(bool(0))
    wb_adr_o = Signal(intbv(0)[WB_ADDR_WIDTH:])
    wb_dat_o = Signal(intbv(0)[WB_DATA_WIDTH:])
    wb_we_o = Signal(bool(0))
    wb_sel_o = Signal(intbv(0)[WB_SELECT_WIDTH:])
    wb_stb_o = Signal(bool(0))
    wb_cyc_o = Signal(bool(0))
    busy = Signal(bool(0))

    # sources and sinks
    source_pause = Signal(bool(0))
    sink_pause = Signal(bool(0))

    source = axis_ep.AXIStreamSource()

    source_logic = source.create_logic(
        clk,
        rst,
        tdata=input_axis_tdata,
        tkeep=input_axis_tkeep,
        tvalid=input_axis_tvalid,
        tready=input_axis_tready,
        tlast=input_axis_tlast,
        tuser=input_axis_tuser,
        pause=source_pause,
        name='source'
    )

    sink = axis_ep.AXIStreamSink()

    sink_logic = sink.create_logic(
        clk,
        rst,
        tdata=output_axis_tdata,
        tkeep=output_axis_tkeep,
        tvalid=output_axis_tvalid,
        tready=output_axis_tready,
        tlast=output_axis_tlast,
        tuser=output_axis_tuser,
        pause=sink_pause,
        name='sink'
    )

    # WB RAM model
    wb_ram_inst = wb.WBRam(2**16)

    wb_ram_port0 = wb_ram_inst.create_port(
        clk,
        adr_i=wb_adr_o,
        dat_i=wb_dat_o,
        dat_o=wb_dat_i,
        we_i=wb_we_o,
        sel_i=wb_sel_o,
        stb_i=wb_stb_o,
        ack_o=wb_ack_i,
        cyc_i=wb_cyc_o,
        latency=1,
        asynchronous=False,
        name='port0'
    )

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,

        input_axis_tdata=input_axis_tdata,
        input_axis_tkeep=input_axis_tkeep,
        input_axis_tvalid=input_axis_tvalid,
        input_axis_tready=input_axis_tready,
        input_axis_tlast=input_axis_tlast,
        input_axis_tuser=input_axis_tuser,

        output_axis_tdata=output_axis_tdata,
        output_axis_tkeep=output_axis_tkeep,
        output_axis_tvalid=output_axis_tvalid,
        output_axis_tready=output_axis_tready,
        output_axis_tlast=output_axis_tlast,
        output_axis_tuser=output_axis_tuser,

        wb_adr_o=wb_adr_o,
        wb_dat_i=wb_dat_i,
        wb_dat_o=wb_dat_o,
        wb_we_o=wb_we_o,
        wb_sel_o=wb_sel_o,
        wb_stb_o=wb_stb_o,
        wb_ack_i=wb_ack_i,
        wb_err_i=wb_err_i,
        wb_cyc_o=wb_cyc_o,

        busy=busy
    )

    @always(delay(4))
    def clkgen():
        clk.next = not clk

    @instance
    def check():
        yield delay(100)
        yield clk.posedge
        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge
        yield delay(100)
        yield clk.posedge

        # testbench stimulus

        yield clk.posedge
        print("test 1: test write")
        current_test.next = 1

        source.write(bytearray(b'\xA2'+struct.pack('>IH', 0, 4)+b'\x11\x22\x33\x44'))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(0, 4) == b'\x11\x22\x33\x44'

        rx_data = bytearray(sink.read())
        print(repr(rx_data))
        assert rx_data == b'\xA4'+struct.pack('>IH', 0, 4)

        yield delay(100)

        yield clk.posedge
        print("test 2: test read")
        current_test.next = 2

        source.write(bytearray(b'\xA1'+struct.pack('>IH', 0, 4)))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        rx_data = bytearray(sink.read())
        print(repr(rx_data))
        assert rx_data == b'\xA3'+struct.pack('>IH', 0, 4)+b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 3: various writes")
        current_test.next = 3

        for length in range(1,9):
            for offset in range(4,8):
                wb_ram_inst.write_mem(256*(16*offset+length), b'\xAA'*16)
                source.write(bytearray(b'\xA2'+struct.pack('>IH', 256*(16*offset+length)+offset, length)+b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]))
                yield clk.posedge

                yield input_axis_tvalid.negedge

                yield delay(200)

                yield clk.posedge

                data = wb_ram_inst.read_mem(256*(16*offset+length), 32)
                for i in range(0, len(data), 16):
                    print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset, length) == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]
                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset-1, 1) == b'\xAA'
                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset+length, 1) == b'\xAA'

                rx_data = bytearray(sink.read())
                print(repr(rx_data))
                assert rx_data == b'\xA4'+struct.pack('>IH', 256*(16*offset+length)+offset, length)

        yield delay(100)

        yield clk.posedge
        print("test 4: various reads")
        current_test.next = 4

        for length in range(1,9):
            for offset in range(4,8):
                source.write(bytearray(b'\xA1'+struct.pack('>IH', 256*(16*offset+length)+offset, length)))
                yield clk.posedge

                yield input_axis_tvalid.negedge

                yield delay(200)

                yield clk.posedge

                rx_data = bytearray(sink.read())
                print(repr(rx_data))
                assert rx_data == b'\xA3'+struct.pack('>IH', 256*(16*offset+length)+offset, length)+b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        yield clk.posedge
        print("test 5: test leading padding")
        current_test.next = 5

        source.write(bytearray(b'\xA2'+struct.pack('>IH', 4, 1)+b'\xAA'))
        source.write(bytearray(b'\x00'*8+b'\xA2'+struct.pack('>IH', 5, 1)+b'\xBB'))
        source.write(bytearray(b'\x00'*8+b'\xA1'+struct.pack('>IH', 4, 1)))
        source.write(bytearray(b'\xA2'+struct.pack('>IH', 6, 1)+b'\xCC'))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(4, 3) == b'\xAA\x00\xCC'

        rx_data = bytearray(sink.read())
        print(repr(rx_data))
        assert rx_data == b'\xA4'+struct.pack('>IH', 4, 1)+b'\xA4'+struct.pack('>IH', 6, 1)

        yield delay(100)

        yield clk.posedge
        print("test 6: test trailing padding")
        current_test.next = 6

        source.write(bytearray(b'\xA2'+struct.pack('>IH', 7, 1)+b'\xAA'))
        source.write(bytearray(b'\xA2'+struct.pack('>IH', 8, 1)+b'\xBB'+b'\x00'*8))
        source.write(bytearray(b'\xA1'+struct.pack('>IH', 7, 1)+b'\x00'*8))
        source.write(bytearray(b'\xA1'+struct.pack('>IH', 7, 1)+b'\x00'*1))
        source.write(bytearray(b'\xA2'+struct.pack('>IH', 9, 1)+b'\xCC'))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(7, 3) == b'\xAA\xBB\xCC'

        rx_data = bytearray(sink.read())
        print(repr(rx_data))
        assert rx_data == b'\xA4'+struct.pack('>IH', 7, 1)+\
                            b'\xA4'+struct.pack('>IH', 8, 1)+\
                            b'\xA3'+struct.pack('>IH', 7, 1)+b'\xAA'+\
                            b'\xA3'+struct.pack('>IH', 7, 1)+b'\xAA'+\
                            b'\xA4'+struct.pack('>IH', 9, 1)

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
