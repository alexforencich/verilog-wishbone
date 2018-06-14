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

module = 'wb_dp_ram'
testbench = 'test_%s' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    DATA_WIDTH = 32
    ADDR_WIDTH = 32
    SELECT_WIDTH = 4

    # Inputs
    a_clk = Signal(bool(0))
    a_rst = Signal(bool(0))
    b_clk = Signal(bool(0))
    b_rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    a_adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    a_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    a_we_i = Signal(bool(0))
    a_sel_i = Signal(intbv(0)[SELECT_WIDTH:])
    a_stb_i = Signal(bool(0))
    a_cyc_i = Signal(bool(0))
    b_adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    b_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    b_we_i = Signal(bool(0))
    b_sel_i = Signal(intbv(0)[SELECT_WIDTH:])
    b_stb_i = Signal(bool(0))
    b_cyc_i = Signal(bool(0))

    # Outputs
    a_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    a_ack_o = Signal(bool(0))
    b_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    b_ack_o = Signal(bool(0))

    # WB master A
    wbm_inst_a = wb.WBMaster()

    wbm_logic_a = wbm_inst_a.create_logic(
        a_clk,
        adr_o=a_adr_i,
        dat_i=a_dat_o,
        dat_o=a_dat_i,
        we_o=a_we_i,
        sel_o=a_sel_i,
        stb_o=a_stb_i,
        ack_i=a_ack_o,
        cyc_o=a_cyc_i,
        name='master_a'
    )

    # WB master B
    wbm_inst_b = wb.WBMaster()

    wbm_logic_b = wbm_inst_b.create_logic(
        b_clk,
        adr_o=b_adr_i,
        dat_i=b_dat_o,
        dat_o=b_dat_i,
        we_o=b_we_i,
        sel_o=b_sel_i,
        stb_o=b_stb_i,
        ack_i=b_ack_o,
        cyc_o=b_cyc_i,
        name='master_'
    )

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        a_clk=a_clk,
        a_rst=a_rst,
        b_clk=b_clk,
        b_rst=b_rst,
        current_test=current_test,
        a_adr_i=a_adr_i,
        a_dat_i=a_dat_i,
        a_dat_o=a_dat_o,
        a_we_i=a_we_i,
        a_sel_i=a_sel_i,
        a_stb_i=a_stb_i,
        a_ack_o=a_ack_o,
        a_cyc_i=a_cyc_i,
        b_adr_i=b_adr_i,
        b_dat_i=b_dat_i,
        b_dat_o=b_dat_o,
        b_we_i=b_we_i,
        b_sel_i=b_sel_i,
        b_stb_i=b_stb_i,
        b_ack_o=b_ack_o,
        b_cyc_i=b_cyc_i
    )

    @always(delay(4))
    def a_clkgen():
        a_clk.next = not a_clk

    @always(delay(5))
    def b_clkgen():
        b_clk.next = not b_clk

    @instance
    def check():
        yield delay(100)
        yield a_clk.posedge
        a_rst.next = 1
        b_rst.next = 1
        yield a_clk.posedge
        yield a_clk.posedge
        yield a_clk.posedge
        a_rst.next = 0
        b_rst.next = 0
        yield a_clk.posedge
        yield delay(100)
        yield a_clk.posedge

        yield a_clk.posedge
        print("test 1: read and write (port A)")
        current_test.next = 1

        wbm_inst_a.init_write(4, b'\x11\x22\x33\x44')

        yield wbm_inst_a.wait()
        yield a_clk.posedge

        wbm_inst_a.init_read(4, 4)

        yield wbm_inst_a.wait()
        yield a_clk.posedge

        data = wbm_inst_a.get_read_data()
        assert data[0] == 4
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield a_clk.posedge
        print("test 2: read and write (port B)")
        current_test.next = 2

        wbm_inst_b.init_write(4, b'\x11\x22\x33\x44')

        yield wbm_inst_b.wait()
        yield b_clk.posedge

        wbm_inst_b.init_read(4, 4)

        yield wbm_inst_b.wait()
        yield b_clk.posedge

        data = wbm_inst_b.get_read_data()
        assert data[0] == 4
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield a_clk.posedge
        print("test 3: various reads and writes (port A)")
        current_test.next = 3

        for length in range(1,8):
            for offset in range(4):
                wbm_inst_a.init_write(256*(16*offset+length)+offset, b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length])

                yield wbm_inst_a.wait()
                yield a_clk.posedge

        for length in range(1,8):
            for offset in range(4):
                wbm_inst_a.init_read(256*(16*offset+length)+offset, length)

                yield wbm_inst_a.wait()
                yield a_clk.posedge

                data = wbm_inst_a.get_read_data()
                assert data[0] == 256*(16*offset+length)+offset
                assert data[1] == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        yield a_clk.posedge
        print("test 4: various reads and writes (port B)")
        current_test.next = 4

        for length in range(1,8):
            for offset in range(4):
                wbm_inst_b.init_write(256*(16*offset+length)+offset, b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length])

                yield wbm_inst_b.wait()
                yield b_clk.posedge

        for length in range(1,8):
            for offset in range(4):
                wbm_inst_b.init_read(256*(16*offset+length)+offset, length)

                yield wbm_inst_b.wait()
                yield b_clk.posedge

                data = wbm_inst_b.get_read_data()
                assert data[0] == 256*(16*offset+length)+offset
                assert data[1] == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        yield a_clk.posedge
        print("test 5: simultaneous read and write")
        current_test.next = 5

        wbm_inst_a.init_write(8, b'\xAA\xAA\xAA\xAA')
        wbm_inst_b.init_write(12, b'\xBB\xBB\xBB\xBB')

        yield wbm_inst_a.wait()
        yield wbm_inst_b.wait()
        yield a_clk.posedge

        wbm_inst_a.init_read(12, 4)
        wbm_inst_b.init_read(8, 4)

        yield wbm_inst_a.wait()
        yield wbm_inst_b.wait()
        yield a_clk.posedge

        data = wbm_inst_a.get_read_data()
        assert data[0] == 12
        assert data[1] == b'\xBB\xBB\xBB\xBB'
        data = wbm_inst_b.get_read_data()
        assert data[0] == 8
        assert data[1] == b'\xAA\xAA\xAA\xAA'

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
