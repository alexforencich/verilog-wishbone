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

module = 'wb_mux_2'
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
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    wbm_adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    wbm_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    wbm_we_i = Signal(bool(0))
    wbm_sel_i = Signal(intbv(0)[SELECT_WIDTH:])
    wbm_stb_i = Signal(bool(0))
    wbm_cyc_i = Signal(bool(0))
    wbs0_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    wbs0_ack_i = Signal(bool(0))
    wbs0_err_i = Signal(bool(0))
    wbs0_rty_i = Signal(bool(0))
    wbs0_addr = Signal(intbv(0)[ADDR_WIDTH:])
    wbs0_addr_msk = Signal(intbv(0)[ADDR_WIDTH:])
    wbs1_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    wbs1_ack_i = Signal(bool(0))
    wbs1_err_i = Signal(bool(0))
    wbs1_rty_i = Signal(bool(0))
    wbs1_addr = Signal(intbv(0)[ADDR_WIDTH:])
    wbs1_addr_msk = Signal(intbv(0)[ADDR_WIDTH:])

    # Outputs
    wbm_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    wbm_ack_o = Signal(bool(0))
    wbm_err_o = Signal(bool(0))
    wbm_rty_o = Signal(bool(0))
    wbs0_adr_o = Signal(intbv(0)[ADDR_WIDTH:])
    wbs0_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    wbs0_we_o = Signal(bool(0))
    wbs0_sel_o = Signal(intbv(0)[SELECT_WIDTH:])
    wbs0_stb_o = Signal(bool(0))
    wbs0_cyc_o = Signal(bool(0))
    wbs1_adr_o = Signal(intbv(0)[ADDR_WIDTH:])
    wbs1_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    wbs1_we_o = Signal(bool(0))
    wbs1_sel_o = Signal(intbv(0)[SELECT_WIDTH:])
    wbs1_stb_o = Signal(bool(0))
    wbs1_cyc_o = Signal(bool(0))

    # WB master
    wbm_inst = wb.WBMaster()

    wbm_logic = wbm_inst.create_logic(
        clk,
        adr_o=wbm_adr_i,
        dat_i=wbm_dat_o,
        dat_o=wbm_dat_i,
        we_o=wbm_we_i,
        sel_o=wbm_sel_i,
        stb_o=wbm_stb_i,
        ack_i=wbm_ack_o,
        cyc_o=wbm_cyc_i,
        name='master'
    )

    # WB RAM model
    wb_ram0_inst = wb.WBRam(2**16)

    wb_ram0_port0 = wb_ram0_inst.create_port(
        clk,
        adr_i=wbs0_adr_o,
        dat_i=wbs0_dat_o,
        dat_o=wbs0_dat_i,
        we_i=wbs0_we_o,
        sel_i=wbs0_sel_o,
        stb_i=wbs0_stb_o,
        ack_o=wbs0_ack_i,
        cyc_i=wbs0_cyc_o,
        latency=1,
        asynchronous=False,
        name='slave0'
    )

    # WB RAM model
    wb_ram1_inst = wb.WBRam(2**16)

    wb_ram1_port0 = wb_ram1_inst.create_port(
        clk,
        adr_i=wbs1_adr_o,
        dat_i=wbs1_dat_o,
        dat_o=wbs1_dat_i,
        we_i=wbs1_we_o,
        sel_i=wbs1_sel_o,
        stb_i=wbs1_stb_o,
        ack_o=wbs1_ack_i,
        cyc_i=wbs1_cyc_o,
        latency=1,
        asynchronous=False,
        name='slave1'
    )

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,
        wbm_adr_i=wbm_adr_i,
        wbm_dat_i=wbm_dat_i,
        wbm_dat_o=wbm_dat_o,
        wbm_we_i=wbm_we_i,
        wbm_sel_i=wbm_sel_i,
        wbm_stb_i=wbm_stb_i,
        wbm_ack_o=wbm_ack_o,
        wbm_err_o=wbm_err_o,
        wbm_rty_o=wbm_rty_o,
        wbm_cyc_i=wbm_cyc_i,
        wbs0_adr_o=wbs0_adr_o,
        wbs0_dat_i=wbs0_dat_i,
        wbs0_dat_o=wbs0_dat_o,
        wbs0_we_o=wbs0_we_o,
        wbs0_sel_o=wbs0_sel_o,
        wbs0_stb_o=wbs0_stb_o,
        wbs0_ack_i=wbs0_ack_i,
        wbs0_err_i=wbs0_err_i,
        wbs0_rty_i=wbs0_rty_i,
        wbs0_cyc_o=wbs0_cyc_o,
        wbs0_addr=wbs0_addr,
        wbs0_addr_msk=wbs0_addr_msk,
        wbs1_adr_o=wbs1_adr_o,
        wbs1_dat_i=wbs1_dat_i,
        wbs1_dat_o=wbs1_dat_o,
        wbs1_we_o=wbs1_we_o,
        wbs1_sel_o=wbs1_sel_o,
        wbs1_stb_o=wbs1_stb_o,
        wbs1_ack_i=wbs1_ack_i,
        wbs1_err_i=wbs1_err_i,
        wbs1_rty_i=wbs1_rty_i,
        wbs1_cyc_o=wbs1_cyc_o,
        wbs1_addr=wbs1_addr,
        wbs1_addr_msk=wbs1_addr_msk
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

        wbs0_addr.next = 0x00000000
        wbs0_addr_msk.next = 0xFFFF0000

        wbs1_addr.next = 0x00010000
        wbs1_addr_msk.next = 0xFFFF0000

        yield clk.posedge
        print("test 1: write to slave 0")
        current_test.next = 1

        wbm_inst.init_write(0x00000004, b'\x11\x22\x33\x44')

        yield wbm_inst.wait()
        yield clk.posedge

        data = wb_ram0_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram0_inst.read_mem(4,4) == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 2: read from slave 0")
        current_test.next = 2

        wbm_inst.init_read(0x00000004, 4)

        yield wbm_inst.wait()
        yield clk.posedge

        data = wbm_inst.get_read_data()
        assert data[0] == 0x00000004
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 3: write to slave 1")
        current_test.next = 3

        wbm_inst.init_write(0x00010004, b'\x11\x22\x33\x44')

        yield wbm_inst.wait()
        yield clk.posedge

        data = wb_ram1_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram1_inst.read_mem(4,4) == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 4: read from slave 1")
        current_test.next = 4

        wbm_inst.init_read(0x00010004, 4)

        yield wbm_inst.wait()
        yield clk.posedge

        data = wbm_inst.get_read_data()
        assert data[0] == 0x00010004
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
