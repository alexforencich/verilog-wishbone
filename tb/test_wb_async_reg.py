#!/usr/bin/env python2
"""

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

"""

from myhdl import *
import os

import wb

module = 'wb_async_reg'

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("test_%s.v" % module)

src = ' '.join(srcs)

build_cmd = "iverilog -o test_%s.vvp %s" % (module, src)

def dut_wb_async_reg(m_clk,
                     m_rst,
                     s_clk,
                     s_rst,
                     current_test,
                     m_adr_i,
                     m_dat_i,
                     m_dat_o,
                     m_we_i,
                     m_sel_i,
                     m_stb_i,
                     m_ack_o,
                     m_err_o,
                     m_rty_o,
                     m_cyc_i,
                     s_adr_o,
                     s_dat_i,
                     s_dat_o,
                     s_we_o,
                     s_sel_o,
                     s_stb_o,
                     s_ack_i,
                     s_err_i,
                     s_rty_i,
                     s_cyc_o):

    if os.system(build_cmd):
        raise Exception("Error running build command")
    return Cosimulation("vvp -m myhdl test_%s.vvp -lxt2" % module,
                m_clk=m_clk,
                m_rst=m_rst,
                s_clk=s_clk,
                s_rst=s_rst,
                current_test=current_test,
                m_adr_i=m_adr_i,
                m_dat_i=m_dat_i,
                m_dat_o=m_dat_o,
                m_we_i=m_we_i,
                m_sel_i=m_sel_i,
                m_stb_i=m_stb_i,
                m_ack_o=m_ack_o,
                m_err_o=m_err_o,
                m_rty_o=m_rty_o,
                m_cyc_i=m_cyc_i,
                s_adr_o=s_adr_o,
                s_dat_i=s_dat_i,
                s_dat_o=s_dat_o,
                s_we_o=s_we_o,
                s_sel_o=s_sel_o,
                s_stb_o=s_stb_o,
                s_ack_i=s_ack_i,
                s_err_i=s_err_i,
                s_rty_i=s_rty_i,
                s_cyc_o=s_cyc_o)

def bench():

    # Parameters
    DATA_WIDTH = 32
    ADDR_WIDTH = 32
    SELECT_WIDTH = 4

    # Inputs
    m_clk = Signal(bool(0))
    m_rst = Signal(bool(0))
    s_clk = Signal(bool(0))
    s_rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    m_adr_i = Signal(intbv(0)[ADDR_WIDTH:])
    m_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    m_we_i = Signal(bool(0))
    m_sel_i = Signal(intbv(0)[SELECT_WIDTH:])
    m_stb_i = Signal(bool(0))
    m_cyc_i = Signal(bool(0))
    s_dat_i = Signal(intbv(0)[DATA_WIDTH:])
    s_ack_i = Signal(bool(0))
    s_err_i = Signal(bool(0))
    s_rty_i = Signal(bool(0))

    # Outputs
    m_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    m_ack_o = Signal(bool(0))
    m_err_o = Signal(bool(0))
    m_rty_o = Signal(bool(0))
    s_adr_o = Signal(intbv(0)[ADDR_WIDTH:])
    s_dat_o = Signal(intbv(0)[DATA_WIDTH:])
    s_we_o = Signal(bool(0))
    s_sel_o = Signal(intbv(0)[SELECT_WIDTH:])
    s_stb_o = Signal(bool(0))
    s_cyc_o = Signal(bool(0))

    # WB master
    wbm_inst = wb.WBMaster()

    wbm_logic = wbm_inst.create_logic(m_clk,
                                      adr_o=m_adr_i,
                                      dat_i=m_dat_o,
                                      dat_o=m_dat_i,
                                      we_o=m_we_i,
                                      sel_o=m_sel_i,
                                      stb_o=m_stb_i,
                                      ack_i=m_ack_o,
                                      cyc_o=m_cyc_i,
                                      name='master')

    # WB RAM model
    wb_ram_inst = wb.WBRam(2**16)

    wb_ram_port0 = wb_ram_inst.create_port(s_clk,
                                           adr_i=s_adr_o,
                                           dat_i=s_dat_o,
                                           dat_o=s_dat_i,
                                           we_i=s_we_o,
                                           sel_i=s_sel_o,
                                           stb_i=s_stb_o,
                                           ack_o=s_ack_i,
                                           cyc_i=s_cyc_o,
                                           latency=1,
                                           async=False,
                                           name='slave')

    # DUT
    dut = dut_wb_async_reg(m_clk,
                           m_rst,
                           s_clk,
                           s_rst,
                           current_test,
                           m_adr_i,
                           m_dat_i,
                           m_dat_o,
                           m_we_i,
                           m_sel_i,
                           m_stb_i,
                           m_ack_o,
                           m_err_o,
                           m_rty_o,
                           m_cyc_i,
                           s_adr_o,
                           s_dat_i,
                           s_dat_o,
                           s_we_o,
                           s_sel_o,
                           s_stb_o,
                           s_ack_i,
                           s_err_i,
                           s_rty_i,
                           s_cyc_o)

    @always(delay(4))
    def m_clkgen():
        m_clk.next = not m_clk

    @always(delay(5))
    def s_clkgen():
        s_clk.next = not s_clk

    @instance
    def check():
        yield delay(100)
        yield m_clk.posedge
        m_rst.next = 1
        s_rst.next = 1
        yield m_clk.posedge
        yield m_clk.posedge
        yield m_clk.posedge
        m_rst.next = 0
        s_rst.next = 0
        yield m_clk.posedge
        yield delay(100)
        yield m_clk.posedge

        yield m_clk.posedge
        print("test 1: write")
        current_test.next = 1

        wbm_inst.init_write(4, b'\x11\x22\x33\x44')

        yield m_cyc_i.negedge
        yield m_clk.posedge
        yield m_clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join("{:02x}".format(ord(c)) for c in data[i:i+16]))

        assert wb_ram_inst.read_mem(4,4) == b'\x11\x22\x33\x44'

        yield delay(100)

        yield m_clk.posedge
        print("test 2: read")
        current_test.next = 2

        wbm_inst.init_read(4, 4)

        yield m_cyc_i.negedge
        yield m_clk.posedge
        yield m_clk.posedge

        data = wbm_inst.get_read_data()
        assert data[0] == 4
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield m_clk.posedge
        print("test 3: various writes")
        current_test.next = 3

        for length in range(1,8):
            for offset in range(4):
                wbm_inst.init_write(256*(16*offset+length)+offset, b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length])

                yield m_cyc_i.negedge
                yield m_clk.posedge
                yield m_clk.posedge

                data = wb_ram_inst.read_mem(256*(16*offset+length), 32)
                for i in range(0, len(data), 16):
                    print(" ".join("{:02x}".format(ord(c)) for c in data[i:i+16]))

                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset,length) == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        yield m_clk.posedge
        print("test 4: various reads")
        current_test.next = 4

        for length in range(1,8):
            for offset in range(4):
                wbm_inst.init_read(256*(16*offset+length)+offset, length)

                yield m_cyc_i.negedge
                yield m_clk.posedge
                yield m_clk.posedge

                data = wbm_inst.get_read_data()
                assert data[0] == 256*(16*offset+length)+offset
                assert data[1] == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        raise StopSimulation

    return dut, wbm_logic, wb_ram_port0, m_clkgen, s_clkgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
