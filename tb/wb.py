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
from Queue import Queue
import mmap

class WBMaster(object):
    def __init__(self):
        self.command_queue = Queue()
        self.read_data_queue = Queue()
        self.has_logic = False

    def init_read(self, address, length):
        self.command_queue.put(('r', address, length))

    def init_write(self, address, data):
        self.command_queue.put(('w', address, data))

    def read_data_ready(self):
        return not self.read_data_queue.empty()

    def get_read_data(self):
        return self.read_data_queue.get(False)

    def create_logic(self,
                     clk,
                     adr_o=Signal(intbv(0)[8:]),
                     dat_i=None,
                     dat_o=None,
                     we_o=Signal(bool(0)),
                     sel_o=Signal(intbv(1)[1:]),
                     stb_o=Signal(bool(0)),
                     ack_i=Signal(bool(0)),
                     cyc_o=Signal(bool(0)),
                     name=None):
        
        if self.has_logic:
            raise Exception("Logic already instantiated!")

        self.has_logic = True

        @instance
        def logic():
            if dat_i is not None:
                assert len(dat_i) % 8 == 0
                w = len(dat_i)
            if dat_o is not None:
                assert len(dat_o) % 8 == 0
                w = len(dat_o)
            if dat_i is not None and dat_o is not None:
                assert len(dat_i) == len(dat_o)

            bw = int(w/8)
            ww = len(sel_o)
            ws = bw/ww

            assert ww in (1, 2, 4, 8)
            assert ws in (1, 2, 4, 8)

            while True:
                yield clk.posedge

                # check for commands
                if not self.command_queue.empty():
                    cmd = self.command_queue.get(False)

                    # address in full word width
                    addr = int(cmd[1]/bw)*bw
                    # address in words
                    adw = int(cmd[1]/ws)*ws
                    # select for first access
                    sel_start = ((2**(ww)-1) << (adw/ws) % ww) & (2**(ww)-1)

                    # cannot address within words
                    assert cmd[1] == adw

                    if cmd[0] == 'w':
                        data = cmd[2]
                        # select for last access
                        sel_end = ((2**(ww)-1) >> (ww - (((adw/ws + int(len(data)/ws) - 1) % ww) + 1)))
                        # number of cycles
                        cycles = int((len(data) + bw-1 + (cmd[1] % bw)) / bw)
                        i = 0

                        if name is not None:
                            print("[%s] Write data a:0x%08x d:%s" % (name, adw, " ".join("{:02x}".format(ord(c)) for c in data)))

                        cyc_o.next = 1
                        stb_o.next = 1
                        we_o.next = 1

                        # first cycle
                        adr_o.next = addr
                        val = 0
                        for j in range(bw):
                            if int(j/ws) >= (adw/ws) % ww and (cycles > 1 or int(j/ws) < (((adw/ws + int(len(data)/ws) - 1) % ww) + 1)):
                                val |= ord(data[i]) << j*8
                                i += 1
                        dat_o.next = val

                        if cycles == 1:
                            sel_o.next = sel_start & sel_end
                        else:
                            sel_o.next = sel_start

                        yield clk.posedge

                        while not int(ack_i):
                            yield clk.posedge

                        for k in range(1, cycles-1):
                            # middle cycles
                            adr_o.next = addr + k * bw
                            val = 0
                            for j in range(bw):
                                val |= ord(data[i]) << j*8
                                i += 1
                            dat_o.next = val
                            sel_o.next = 2**(ww)-1

                            yield clk.posedge
                            
                            while not int(ack_i):
                                yield clk.posedge

                        if cycles > 1:
                            # last cycle
                            adr_o.next = addr + (cycles-1) * bw
                            val = 0
                            for j in range(bw):
                                if int(j/ws) < (((adw/ws + int(len(data)/ws) - 1) % ww) + 1):
                                    val |= ord(data[i]) << j*8
                                    i += 1
                            dat_o.next = val
                            sel_o.next = sel_end

                            yield clk.posedge

                            while not int(ack_i):
                                yield clk.posedge

                        we_o.next = 0

                        cyc_o.next = 0
                        stb_o.next = 0
                    elif cmd[0] == 'r':
                        data = b''
                        # select for last access
                        sel_end = ((2**(ww)-1) >> (ww - (((adw/ws + int(cmd[2]/ws) - 1) % ww) + 1)))
                        # number of cycles
                        cycles = int((cmd[2] + bw-1 + (cmd[1] % bw)) / bw)

                        cyc_o.next = 1
                        stb_o.next = 1

                        # first cycle
                        adr_o.next = addr
                        if cycles == 1:
                            sel_o.next = sel_start & sel_end
                        else:
                            sel_o.next = sel_start

                        while not int(ack_i):
                            yield clk.posedge

                        val = int(dat_i)

                        for j in range(bw):
                            if int(j/ws) >= (adw/ws) % ww and (cycles > 1 or int(j/ws) < (((adw/ws + int(cmd[2]/ws) - 1) % ww) + 1)):
                                data += chr((val >> j*8) & 255)

                        for k in range(1, cycles-1):
                            # middle cycles
                            adr_o.next = addr + k * bw
                            sel_o.next = 2**(ww)-1

                            yield clk.posedge

                            while not int(ack_i):
                                yield clk.posedge

                            val = int(dat_i)

                            for j in range(bw):
                                data += chr((val >> j*8) & 255)

                        if cycles > 1:
                            # last cycle
                            adr_o.next = addr + (cycles-1) * bw
                            sel_o.next = sel_end

                            yield clk.posedge

                            while not int(ack_i):
                                yield clk.posedge

                            val = int(dat_i)

                            for j in range(bw):
                                if int(j/ws) < (((adw/ws + int(cmd[2]/ws) - 1) % ww) + 1):
                                    data += chr((val >> j*8) & 255)

                        cyc_o.next = 0
                        stb_o.next = 0

                        if name is not None:
                            print("[%s] Read data a:0x%08x d:%s" % (name, adw, " ".join("{:02x}".format(ord(c)) for c in data)))

                        self.read_data_queue.put((adw, data))

        return logic


class WBRam(object):
    def __init__(self, size = 1024):
        self.size = size
        self.mem = mmap.mmap(-1, size)

    def read_mem(self, address, length):
        self.mem.seek(address)
        return self.mem.read(length)

    def write_mem(self, address, data):
        self.mem.seek(address)
        self.mem.write(data)

    def create_port(self,
                    clk,
                    adr_i=Signal(intbv(0)[8:]),
                    dat_i=None,
                    dat_o=None,
                    we_i=Signal(bool(0)),
                    sel_i=Signal(intbv(1)[1:]),
                    stb_i=Signal(bool(0)),
                    ack_o=Signal(bool(0)),
                    cyc_i=Signal(bool(0)),
                    latency=1,
                    async=False,
                    name=None):

        @instance
        def logic():
            if dat_i is not None:
                assert len(dat_i) % 8 == 0
                w = len(dat_i)
            if dat_o is not None:
                assert len(dat_o) % 8 == 0
                w = len(dat_o)
            if dat_i is not None and dat_o is not None:
                assert len(dat_i) == len(dat_o)

            bw = int(w/8)
            ww = len(sel_i)
            ws = bw/ww

            assert ww in (1, 2, 4, 8)
            assert ws in (1, 2, 4, 8)

            while True:
                if async:
                    yield adr_i, cyc_i, stb_i
                else:
                    yield clk.posedge

                ack_o.next = False

                addr = int(adr_i/bw)*bw

                if cyc_i & stb_i & ~ack_o:
                    if async:
                        yield delay(latency)
                    else:
                        for i in range(latency):
                            yield clk.posedge
                    ack_o.next = True
                    self.mem.seek(addr % self.size)
                    if we_i:
                        # write
                        #yield clk.posedge
                        data = []
                        val = int(dat_i)
                        for i in range(bw):
                            data.append(bytes(bytearray([val & 0xff])))
                            val >>= 8
                        for i in range(ww):
                            for j in range(ws):
                                if sel_i & (1 << i):
                                    self.mem.write(data[i*ws+j])
                                else:
                                    self.mem.seek(1, 1)
                        if name is not None:
                            print("[%s] Write word a:0x%08x sel:0x%02x d:%s" % (name, addr, sel_i, " ".join("{:02x}".format(ord(c)) for c in data)))
                    else:
                        data = self.mem.read(bw)
                        val = 0
                        for i in range(bw-1,-1,-1):
                            val <<= 8
                            val += ord(data[i])
                        dat_o.next = val
                        if name is not None:
                            print("[%s] Read word a:0x%08x d:%s" % (name, addr, " ".join("{:02x}".format(ord(c)) for c in data)))

        return logic

