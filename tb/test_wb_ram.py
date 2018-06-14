#!/usr/bin/env python
"""

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

"""

from myhdl import *
import os

import wb

module = 'wb_ram'
testbench = 'test_%s' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    DATA_WIDTH = 32
    ADDR_WIDTH = 16
    SELECT_WIDTH = 4

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    dat_i = Signal(intbv(0)[DATA_WIDTH:])
    we_i = Signal(bool(0))
    sel_i = Signal(intbv(0)[SELECT_WIDTH:])
    stb_i = Signal(bool(0))
    cyc_i = Signal(bool(0))

    # Outputs
    dat_o = Signal(intbv(0)[DATA_WIDTH:])
    ack_o = Signal(bool(0))

    # WB master
    wbm_inst = wb.WBMaster()

    wbm_logic = wbm_inst.create_logic(
        clk,
        adr_o=adr_i,
        dat_i=dat_o,
        dat_o=dat_i,
        we_o=we_i,
        sel_o=sel_i,
        stb_o=stb_i,
        ack_i=ack_o,
        cyc_o=cyc_i,
        name='master'
    )

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,
        adr_i=adr_i,
        dat_i=dat_i,
        dat_o=dat_o,
        we_i=we_i,
        sel_i=sel_i,
        stb_i=stb_i,
        ack_o=ack_o,
        cyc_i=cyc_i
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

        yield clk.posedge
        print("test 1: read and write")
        current_test.next = 1

        wbm_inst.init_write(4, b'\x11\x22\x33\x44')

        yield wbm_inst.wait()
        yield clk.posedge

        wbm_inst.init_read(4, 4)

        yield wbm_inst.wait()
        yield clk.posedge

        data = wbm_inst.get_read_data()
        assert data[0] == 4
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 2: various reads and writes")
        current_test.next = 2

        for length in range(1,8):
            for offset in range(4):
                wbm_inst.init_write(256*(16*offset+length)+offset, b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length])

                yield wbm_inst.wait()
                yield clk.posedge

        for length in range(1,8):
            for offset in range(4):
                wbm_inst.init_read(256*(16*offset+length)+offset, length)

                yield wbm_inst.wait()
                yield clk.posedge

                data = wbm_inst.get_read_data()
                assert data[0] == 256*(16*offset+length)+offset
                assert data[1] == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
