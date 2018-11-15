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

module = 'wb_adapter'
testbench = 'test_%s_32_16' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("../rtl/priority_encoder.v")
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    ADDR_WIDTH = 32
    WBM_DATA_WIDTH = 32
    WBM_SELECT_WIDTH = 4
    WBS_DATA_WIDTH = 16
    WBS_SELECT_WIDTH = 2

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    wbm_adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    wbm_dat_i = Signal(intbv(0)[WBM_DATA_WIDTH:])
    wbm_we_i = Signal(bool(0))
    wbm_sel_i = Signal(intbv(0)[WBM_SELECT_WIDTH:])
    wbm_stb_i = Signal(bool(0))
    wbm_cyc_i = Signal(bool(0))
    wbs_dat_i = Signal(intbv(0)[WBS_DATA_WIDTH:])
    wbs_ack_i = Signal(bool(0))
    wbs_err_i = Signal(bool(0))
    wbs_rty_i = Signal(bool(0))

    # Outputs
    wbm_dat_o = Signal(intbv(0)[WBM_DATA_WIDTH:])
    wbm_ack_o = Signal(bool(0))
    wbm_err_o = Signal(bool(0))
    wbm_rty_o = Signal(bool(0))
    wbs_adr_o = Signal(intbv(0)[ADDR_WIDTH:])
    wbs_dat_o = Signal(intbv(0)[WBS_DATA_WIDTH:])
    wbs_we_o = Signal(bool(0))
    wbs_sel_o = Signal(intbv(0)[WBS_SELECT_WIDTH:])
    wbs_stb_o = Signal(bool(0))
    wbs_cyc_o = Signal(bool(0))

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

        yield clk.posedge
        print("test 1: write")
        current_test.next = 1

        wbm_inst.init_write(4, b'\x11\x22\x33\x44')

        yield wbm_inst.wait()
        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(4,4) == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 2: read")
        current_test.next = 2

        wbm_inst.init_read(4, 4)

        yield wbm_inst.wait()
        yield clk.posedge

        data = wbm_inst.get_read_data()
        assert data[0] == 4
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 3: various writes")
        current_test.next = 3

        for length in range(1,8):
            for offset in range(4,8):
                wb_ram_inst.write_mem(256*(16*offset+length), b'\xAA'*32)
                wbm_inst.init_write(256*(16*offset+length)+offset, b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length])

                yield wbm_inst.wait()
                yield clk.posedge

                data = wb_ram_inst.read_mem(256*(16*offset+length), 32)
                for i in range(0, len(data), 16):
                    print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset, length) == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]
                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset-1, 1) == b'\xAA'
                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset+length, 1) == b'\xAA'

        yield delay(100)

        yield clk.posedge
        print("test 4: various reads")
        current_test.next = 4

        for length in range(1,8):
            for offset in range(4,8):
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
