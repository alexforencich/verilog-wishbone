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

module = 'wb_arbiter_2'
testbench = 'test_%s' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("../rtl/arbiter.v")
srcs.append("../rtl/priority_encoder.v")
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    DATA_WIDTH = 32
    ADDR_WIDTH = 32
    SELECT_WIDTH = (DATA_WIDTH/8)
    ARB_TYPE = "PRIORITY"
    LSB_PRIORITY = "HIGH"

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    wbm0_adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    wbm0_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    wbm0_we_i = Signal(bool(0))
    wbm0_sel_i = Signal(intbv(0)[SELECT_WIDTH:])
    wbm0_stb_i = Signal(bool(0))
    wbm0_cyc_i = Signal(bool(0))
    wbm1_adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    wbm1_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    wbm1_we_i = Signal(bool(0))
    wbm1_sel_i = Signal(intbv(0)[SELECT_WIDTH:])
    wbm1_stb_i = Signal(bool(0))
    wbm1_cyc_i = Signal(bool(0))
    wbs_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    wbs_ack_i = Signal(bool(0))
    wbs_err_i = Signal(bool(0))
    wbs_rty_i = Signal(bool(0))

    # Outputs
    wbm0_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    wbm0_ack_o = Signal(bool(0))
    wbm0_err_o = Signal(bool(0))
    wbm0_rty_o = Signal(bool(0))
    wbm1_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    wbm1_ack_o = Signal(bool(0))
    wbm1_err_o = Signal(bool(0))
    wbm1_rty_o = Signal(bool(0))
    wbs_adr_o = Signal(intbv(0)[ADDR_WIDTH:])
    wbs_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    wbs_we_o = Signal(bool(0))
    wbs_sel_o = Signal(intbv(0)[SELECT_WIDTH:])
    wbs_stb_o = Signal(bool(0))
    wbs_cyc_o = Signal(bool(0))

    # WB master
    wbm0_inst = wb.WBMaster()

    wbm0_logic = wbm0_inst.create_logic(
        clk,
        adr_o=wbm0_adr_i,
        dat_i=wbm0_dat_o,
        dat_o=wbm0_dat_i,
        we_o=wbm0_we_i,
        sel_o=wbm0_sel_i,
        stb_o=wbm0_stb_i,
        ack_i=wbm0_ack_o,
        cyc_o=wbm0_cyc_i,
        name='master0'
    )

    # WB master
    wbm1_inst = wb.WBMaster()

    wbm1_logic = wbm1_inst.create_logic(
        clk,
        adr_o=wbm1_adr_i,
        dat_i=wbm1_dat_o,
        dat_o=wbm1_dat_i,
        we_o=wbm1_we_i,
        sel_o=wbm1_sel_i,
        stb_o=wbm1_stb_i,
        ack_i=wbm1_ack_o,
        cyc_o=wbm1_cyc_i,
        name='master1'
    )

    # WB RAM model
    wb_ram_inst = wb.WBRam(2**16)

    wb_ram_port0 = wb_ram_inst.create_port(
        clk,
        adr_i=wbs_adr_o,
        dat_i=wbs_dat_o,
        dat_o=wbs_dat_i,
        we_i=wbs_we_o,
        sel_i=wbs_sel_o,
        stb_i=wbs_stb_o,
        ack_o=wbs_ack_i,
        cyc_i=wbs_cyc_o,
        latency=1,
        asynchronous=False,
        name='slave'
    )

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,

        wbm0_adr_i=wbm0_adr_i,
        wbm0_dat_i=wbm0_dat_i,
        wbm0_dat_o=wbm0_dat_o,
        wbm0_we_i=wbm0_we_i,
        wbm0_sel_i=wbm0_sel_i,
        wbm0_stb_i=wbm0_stb_i,
        wbm0_ack_o=wbm0_ack_o,
        wbm0_err_o=wbm0_err_o,
        wbm0_rty_o=wbm0_rty_o,
        wbm0_cyc_i=wbm0_cyc_i,

        wbm1_adr_i=wbm1_adr_i,
        wbm1_dat_i=wbm1_dat_i,
        wbm1_dat_o=wbm1_dat_o,
        wbm1_we_i=wbm1_we_i,
        wbm1_sel_i=wbm1_sel_i,
        wbm1_stb_i=wbm1_stb_i,
        wbm1_ack_o=wbm1_ack_o,
        wbm1_err_o=wbm1_err_o,
        wbm1_rty_o=wbm1_rty_o,
        wbm1_cyc_i=wbm1_cyc_i,

        wbs_adr_o=wbs_adr_o,
        wbs_dat_i=wbs_dat_i,
        wbs_dat_o=wbs_dat_o,
        wbs_we_o=wbs_we_o,
        wbs_sel_o=wbs_sel_o,
        wbs_stb_o=wbs_stb_o,
        wbs_ack_i=wbs_ack_i,
        wbs_err_i=wbs_err_i,
        wbs_rty_i=wbs_rty_i,
        wbs_cyc_o=wbs_cyc_o
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
        print("test 1: master 0")
        current_test.next = 1

        wbm0_inst.init_write(0x00000000, b'\x11\x22\x33\x44')

        yield wbm0_inst.wait()
        yield clk.posedge

        data = wb_ram_inst.read_mem(0x00000000, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(0,4) == b'\x11\x22\x33\x44'

        wbm0_inst.init_read(0x00000000, 4)

        yield wbm0_inst.wait()
        yield clk.posedge

        data = wbm0_inst.get_read_data()
        assert data[0] == 0x00000000
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 2: master 1")
        current_test.next = 2

        wbm1_inst.init_write(0x00001000, b'\x11\x22\x33\x44')

        yield wbm1_inst.wait()
        yield clk.posedge

        data = wb_ram_inst.read_mem(0x00001000, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(0,4) == b'\x11\x22\x33\x44'

        wbm1_inst.init_read(0x00001000, 4)

        yield wbm0_inst.wait()
        yield wbm1_inst.wait()
        yield clk.posedge

        data = wbm1_inst.get_read_data()
        assert data[0] == 0x00001000
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 3: arbitration")
        current_test.next = 3

        wbm0_inst.init_write(0x00000010, bytearray(range(16)))
        wbm0_inst.init_write(0x00000020, bytearray(range(16)))
        wbm1_inst.init_write(0x00001010, bytearray(range(16)))
        wbm1_inst.init_write(0x00001020, bytearray(range(16)))

        yield wbm1_inst.wait()
        yield clk.posedge

        data = wb_ram_inst.read_mem(0x00000010, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        data = wb_ram_inst.read_mem(0x00001010, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(0,4) == b'\x11\x22\x33\x44'

        wbm0_inst.init_read(0x00000010, 16)
        wbm0_inst.init_read(0x00000020, 16)
        wbm1_inst.init_read(0x00001010, 16)
        wbm1_inst.init_read(0x00001020, 16)

        yield wbm0_inst.wait()
        yield wbm1_inst.wait()
        yield clk.posedge

        data = wbm0_inst.get_read_data()
        assert data[0] == 0x00000010
        assert data[1] == bytearray(range(16))

        data = wbm0_inst.get_read_data()
        assert data[0] == 0x00000020
        assert data[1] == bytearray(range(16))

        data = wbm1_inst.get_read_data()
        assert data[0] == 0x00001010
        assert data[1] == bytearray(range(16))

        data = wbm1_inst.get_read_data()
        assert data[0] == 0x00001020
        assert data[1] == bytearray(range(16))

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
