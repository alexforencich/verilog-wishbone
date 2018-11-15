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

    # WB master
    wb_master_inst = wb.WBMaster()

    wb_master_logic = wb_master_inst.create_logic(
        clk,
        adr_o=port0_adr_i,
        dat_i=port0_dat_o,
        dat_o=port0_dat_i,
        we_o=port0_we_i,
        sel_o=port0_sel_i,
        stb_o=port0_stb_i,
        ack_i=port0_ack_o,
        cyc_o=port0_cyc_i,
        name='master'
    )

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

        yield clk.posedge
        print("test 3: write via port0")
        current_test.next = 3

        wb_master_inst.init_write(4, b'\x11\x22\x33\x44')

        yield wb_master_inst.wait()
        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(4,4) == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 4: read via port0")
        current_test.next = 4

        wb_master_inst.init_read(4, 4)

        yield wb_master_inst.wait()
        yield clk.posedge

        data = wb_master_inst.get_read_data()
        assert data[0] == 4
        assert data[1] == b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 5: various writes")
        current_test.next = 5

        for length in range(1,8):
            for offset in range(4,8):
                wb_ram_inst.write_mem(256*(16*offset+length), b'\xAA'*32)
                wb_master_inst.init_write(256*(16*offset+length)+offset, b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length])

                yield wb_master_inst.wait()
                yield clk.posedge

                data = wb_ram_inst.read_mem(256*(16*offset+length), 32)
                for i in range(0, len(data), 16):
                    print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset, length) == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]
                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset-1, 1) == b'\xAA'
                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset+length, 1) == b'\xAA'

        yield delay(100)

        yield clk.posedge
        print("test 6: various reads")
        current_test.next = 6

        for length in range(1,8):
            for offset in range(4,8):
                wb_master_inst.init_read(256*(16*offset+length)+offset, length)

                yield wb_master_inst.wait()
                yield clk.posedge

                data = wb_master_inst.get_read_data()
                assert data[0] == 256*(16*offset+length)+offset
                assert data[1] == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        yield clk.posedge
        print("test 7: write words")
        current_test.next = 7

        for offset in range(4):
            wb_master_inst.init_write_words((0x4000+offset*64+0)/2+offset, [0x1234])
            wb_master_inst.init_write_dwords((0x4000+offset*64+16)/4+offset, [0x12345678])
            wb_master_inst.init_write_qwords((0x4000+offset*64+32)/8+offset, [0x1234567887654321])

            yield wb_master_inst.wait()
            yield clk.posedge

            data = wb_ram_inst.read_mem(0x4000+offset*64, 64)
            for i in range(0, len(data), 16):
                print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

            assert wb_ram_inst.read_mem((0x4000+offset*64+0)+offset*2, 2) == b'\x34\x12'
            assert wb_ram_inst.read_mem((0x4000+offset*64+16)+offset*4, 4) == b'\x78\x56\x34\x12'
            assert wb_ram_inst.read_mem((0x4000+offset*64+32)+offset*8, 8) == b'\x21\x43\x65\x87\x78\x56\x34\x12'

            assert wb_ram_inst.read_words((0x4000+offset*64+0)/2+offset, 1)[0] == 0x1234
            assert wb_ram_inst.read_dwords((0x4000+offset*64+16)/4+offset, 1)[0] == 0x12345678
            assert wb_ram_inst.read_qwords((0x4000+offset*64+32)/8+offset, 1)[0] == 0x1234567887654321

        yield delay(100)

        yield clk.posedge
        print("test 8: read words")
        current_test.next = 8

        for offset in range(4):
            wb_master_inst.init_read_words((0x4000+offset*64+0)/2+offset, 1)
            wb_master_inst.init_read_dwords((0x4000+offset*64+16)/4+offset, 1)
            wb_master_inst.init_read_qwords((0x4000+offset*64+32)/8+offset, 1)

            yield wb_master_inst.wait()
            yield clk.posedge

            data = wb_master_inst.get_read_data_words()
            assert data[0] == (0x4000+offset*64+0)/2+offset
            assert data[1][0] == 0x1234

            data = wb_master_inst.get_read_data_dwords()
            assert data[0] == (0x4000+offset*64+16)/4+offset
            assert data[1][0] == 0x12345678

            data = wb_master_inst.get_read_data_qwords()
            assert data[0] == (0x4000+offset*64+32)/8+offset
            assert data[1][0] == 0x1234567887654321

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    #sim = Simulation(bench())
    traceSignals.name = os.path.basename(__file__).rsplit('.',1)[0]
    sim = Simulation(traceSignals(bench))
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()

