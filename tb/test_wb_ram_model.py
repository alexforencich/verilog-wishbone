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

def bench():

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    port0_adr_i = Signal(intbv(0)[32:])
    port0_dat_i = Signal(intbv(0)[32:])
    port0_we_i = Signal(bool(0))
    port0_sel_i = Signal(intbv(0)[4:])
    port0_stb_i = Signal(bool(0))
    port0_cyc_i = Signal(bool(0))

    # Outputs
    port0_dat_o = Signal(intbv(0)[32:])
    port0_ack_o = Signal(bool(0))

    # WB RAM model
    wb_ram_inst = wb.WBRam(2**16)

    wb_ram_port0 = wb_ram_inst.create_port(
        clk,
        adr_i=port0_adr_i,
        dat_i=port0_dat_i,
        dat_o=port0_dat_o,
        we_i=port0_we_i,
        sel_i=port0_sel_i,
        stb_i=port0_stb_i,
        ack_o=port0_ack_o,
        cyc_i=port0_cyc_i,
        latency=1,
        asynchronous=False,
        name='port0'
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
        print("test 1: baseline")
        current_test.next = 1

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        yield delay(100)

        yield clk.posedge
        print("test 2: direct write")
        current_test.next = 2

        wb_ram_inst.write_mem(0, b'test')

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(0,4) == b'test'

        yield delay(100)

        yield clk.posedge
        print("test 2: write via port0")
        current_test.next = 2

        yield clk.posedge
        port0_adr_i.next = 4
        port0_dat_i.next = 0x44332211
        port0_sel_i.next = 0xF
        port0_we_i.next = 1

        port0_cyc_i.next = 1
        port0_stb_i.next = 1

        yield port0_ack_o.posedge
        yield clk.posedge
        port0_we_i.next = 0
        port0_cyc_i.next = 0
        port0_stb_i.next = 0

        yield clk.posedge
        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(4,4) == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 3: read via port0")
        current_test.next = 3

        yield clk.posedge
        port0_adr_i.next = 4
        port0_we_i.next = 0

        port0_cyc_i.next = 1
        port0_stb_i.next = 1

        yield port0_ack_o.posedge
        yield clk.posedge
        port0_we_i.next = 0
        port0_cyc_i.next = 0
        port0_stb_i.next = 0

        assert port0_dat_o == 0x44332211

        yield delay(100)

        yield clk.posedge
        print("test 4: various writes")
        current_test.next = 4

        for length in range(1,8):
            for offset in range(4):
                yield clk.posedge
                sel_start = ((2**(4)-1) << offset % 4) & (2**(4)-1)
                sel_end = ((2**(4)-1) >> (4 - (((offset + int(length/1) - 1) % 4) + 1)))
                cycles = int((length + 4-1 + (offset % 4)) / 4)
                i = 1

                port0_cyc_i.next = 1

                port0_stb_i.next = 1
                port0_we_i.next = 1
                port0_adr_i.next = 256*(16*offset+length)
                val = 0
                for j in range(4):
                    if j >= offset % 4 and (cycles > 1 or j < (((offset + int(length/1) - 1) % 4) + 1)):
                        val |= (0x11 * i) << j*8
                        i += 1
                port0_dat_i.next = val
                if cycles == 1:
                    port0_sel_i.next = sel_start & sel_end
                else:
                    port0_sel_i.next = sel_start

                yield clk.posedge
                while not port0_ack_o:
                    yield clk.posedge

                port0_we_i.next = 0
                port0_stb_i.next = 0

                for k in range(1,cycles-1):
                    yield clk.posedge
                    port0_stb_i.next = 1
                    port0_we_i.next = 1
                    port0_adr_i.next = 256*(16*offset+length)+4*k
                    val = 0
                    for j in range(4):
                        val |= (0x11 * i) << j*8
                        i += 1
                    port0_dat_i.next = val
                    port0_sel_i.next = 2**(4)-1

                    yield clk.posedge
                    while not port0_ack_o:
                        yield clk.posedge

                    port0_we_i.next = 0
                    port0_stb_i.next = 0

                if cycles > 1:
                    yield clk.posedge
                    port0_stb_i.next = 1
                    port0_we_i.next = 1
                    port0_adr_i.next = 256*(16*offset+length)+4*(cycles-1)
                    val = 0
                    for j in range(4):
                        if j < (((offset + int(length/1) - 1) % 4) + 1):
                            val |= (0x11 * i) << j*8
                            i += 1
                    port0_dat_i.next = val
                    port0_sel_i.next = sel_end

                    yield clk.posedge
                    while not port0_ack_o:
                        yield clk.posedge

                    port0_we_i.next = 0
                    port0_stb_i.next = 0

                port0_we_i.next = 0
                port0_stb_i.next = 0

                port0_cyc_i.next = 0

                yield clk.posedge
                yield clk.posedge

                data = wb_ram_inst.read_mem(256*(16*offset+length), 32)
                for i in range(0, len(data), 16):
                    print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset,length) == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()

