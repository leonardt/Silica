from magma import *
import os
os.environ["MANTLE"] = os.getenv("MANTLE", "coreir")
from mantle import *
import mantle.common.operator


@cache_definition
def DefineSilicaMux(height, width):
    if "one-hot" == "one-hot":
        if width is None:
            T = Bit
        else:
            T = Bits(width)
        inputs = []
        for i in range(height):
            inputs += [f"I{i}", In(T)]
        class OneHotMux(Circuit):
            name = "SilicaOneHotMux{}{}".format(height, width)
            IO = inputs + ["S", In(Bits(height)), "O", Out(T)]
            @classmethod
            def definition(io):
                or_ = Or(height, width)
                wire(io.O, or_.O)
                for i in range(height):
                    and_ = And(2, width)
                    wire(and_.I0, getattr(io, f"I{i}"))
                    if width is not None:
                        for j in range(width):
                            wire(and_.I1[j], io.S[i])
                    else:
                        wire(and_.I1, io.S[i])
                    wire(getattr(or_, f"I{i}"), and_.O)
        return OneHotMux
    else:
        raise NotImplementedError()


Fifo = DefineCircuit("Fifo", "rdata", Out(Bits(4)), "full", Out(Bit), "empty", Out(Bit), "wdata", In(Bits(4)), "wen", In(Bit), "ren", In(Bit), *ClockInterface(has_ce=False))
Buffer = DefineCircuit("__silica_BufferFifo", "I", In(Bits(8)), "O", Out(Bits(8)))
wire(Buffer.I, Buffer.O)
EndDefine()
__silica_path_state = Buffer()
__silica_yield_state = Register(2, init=1, has_ce=False)

wireclock(Fifo, __silica_yield_state)
wire(bits(1 << 1, 2), __silica_yield_state.I)
wdata = Fifo.wdata
wen = Fifo.wen
ren = Fifo.ren
raddr = Register(2, has_ce=False)
wireclock(Fifo, raddr)
raddr_next = DefineSilicaMux(8, 2)()
wire(__silica_path_state.O, raddr_next.S)
wire(raddr_next.O, raddr.I)
next_empty = DFF(has_ce=False, name="next_empty", init=1)
wireclock(Fifo, next_empty)
next_empty_next = DefineSilicaMux(8, None)()
wire(__silica_path_state.O, next_empty_next.S)
wire(next_empty_next.O, next_empty.I)
memory = [Register(4, has_ce=False) for _ in range(4)]
memory_next = [DefineSilicaMux(8, 4)() for _ in range(4)]
for __silica_i in range(4):
    wire(__silica_path_state.O, memory_next[__silica_i].S)

for __silica_i in range(4):
    wire(memory_next[__silica_i].O, memory[__silica_i].I)
memory_next_0_tmp = []
for __silica_j in range(4):
    memory_next_0_tmp.append(memory[__silica_j].O)
memory_next_1_tmp = []
for __silica_j in range(4):
    memory_next_1_tmp.append(memory[__silica_j].O)
memory_next_2_tmp = []
for __silica_j in range(4):
    memory_next_2_tmp.append(memory[__silica_j].O)
memory_next_3_tmp = []
for __silica_j in range(4):
    memory_next_3_tmp.append(memory[__silica_j].O)
memory_next_4_tmp = []
for __silica_j in range(4):
    memory_next_4_tmp.append(memory[__silica_j].O)
memory_next_5_tmp = []
for __silica_j in range(4):
    memory_next_5_tmp.append(memory[__silica_j].O)
memory_next_6_tmp = []
for __silica_j in range(4):
    memory_next_6_tmp.append(memory[__silica_j].O)
memory_next_7_tmp = []
for __silica_j in range(4):
    memory_next_7_tmp.append(memory[__silica_j].O)
next_full = DFF(has_ce=False, name="next_full", init=0)
wireclock(Fifo, next_full)
next_full_next = DefineSilicaMux(8, None)()
wire(__silica_path_state.O, next_full_next.S)
wire(next_full_next.O, next_full.I)
waddr = Register(2, has_ce=False)
wireclock(Fifo, waddr)
waddr_next = DefineSilicaMux(8, 2)()
wire(__silica_path_state.O, waddr_next.S)
wire(waddr_next.O, waddr.I)
rdata = DefineSilicaMux(8, 4)()
wire(__silica_path_state.O, rdata.S)
wire(rdata.O, Fifo.rdata)
full = DefineSilicaMux(8, None)()
wire(__silica_path_state.O, full.S)
wire(full.O, Fifo.full)
empty = DefineSilicaMux(8, None)()
wire(__silica_path_state.O, empty.S)
wire(empty.O, Fifo.empty)
raddr_next_0_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_0_tmp = next_empty.O
next_full_next_0_tmp = next_full.O
waddr_next_0_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_0_tmp = next_full.O
empty_0_tmp = next_empty.O
rdata_0_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_0 = and_(wen, not_(full_0_tmp))
__silica_decoder_9 = decoder(waddr.O)
for i in range(len(memory)):
    memory_next_0_tmp[i] = DefineSilicaMux(2, len(mux([x.O for x in memory],
        i)))()(mux([x.O for x in memory], i), wdata, bits([not_(
        __silica_decoder_9[i]), __silica_decoder_9[i]]))
waddr_next_0_tmp = add(waddr.O, uint(1, 2))
next_full_next_0_tmp = eq(raddr.O, waddr_next_0_tmp)
next_empty_next_0_tmp = bit(False)
__silica_cond_1 = and_(ren, not_(empty_0_tmp))
raddr_next_0_tmp = add(raddr.O, uint(1, 2))
next_empty_next_0_tmp = eq(raddr_next_0_tmp, waddr_next_0_tmp)
next_full_next_0_tmp = bit(False)
wire(bits(raddr_next_0_tmp), raddr_next.I0)
wire(next_empty_next_0_tmp, next_empty_next.I0)
for __silica_i in range(4):
    wire(memory_next_0_tmp[__silica_i], memory_next[__silica_i].I0)
wire(next_full_next_0_tmp, next_full_next.I0)
wire(bits(waddr_next_0_tmp), waddr_next.I0)
wire(rdata_0_tmp, rdata.I0)
wire(full_0_tmp, full.I0)
wire(empty_0_tmp, empty.I0)
wire(__silica_path_state.I[0], and_(__silica_yield_state.O[0], __silica_cond_0, __silica_cond_1))
raddr_next_1_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_1_tmp = next_empty.O
next_full_next_1_tmp = next_full.O
waddr_next_1_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_1_tmp = next_full.O
empty_1_tmp = next_empty.O
rdata_1_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_2 = and_(wen, not_(full_1_tmp))
__silica_decoder_9 = decoder(waddr.O)
for i in range(len(memory)):
    memory_next_1_tmp[i] = DefineSilicaMux(2, len(mux([x.O for x in memory],
        i)))()(mux([x.O for x in memory], i), wdata, bits([not_(
        __silica_decoder_9[i]), __silica_decoder_9[i]]))
waddr_next_1_tmp = add(waddr.O, uint(1, 2))
next_full_next_1_tmp = eq(raddr.O, waddr_next_1_tmp)
next_empty_next_1_tmp = bit(False)
__silica_cond_3 = not_(and_(ren, not_(empty_1_tmp)))
wire(bits(raddr_next_1_tmp), raddr_next.I1)
wire(next_empty_next_1_tmp, next_empty_next.I1)
for __silica_i in range(4):
    wire(memory_next_1_tmp[__silica_i], memory_next[__silica_i].I1)
wire(next_full_next_1_tmp, next_full_next.I1)
wire(bits(waddr_next_1_tmp), waddr_next.I1)
wire(rdata_1_tmp, rdata.I1)
wire(full_1_tmp, full.I1)
wire(empty_1_tmp, empty.I1)
wire(__silica_path_state.I[1], and_(__silica_yield_state.O[0], __silica_cond_2, __silica_cond_3))
raddr_next_2_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_2_tmp = next_empty.O
next_full_next_2_tmp = next_full.O
waddr_next_2_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_2_tmp = next_full.O
empty_2_tmp = next_empty.O
rdata_2_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_4 = not_(and_(wen, not_(full_2_tmp)))
__silica_cond_5 = and_(ren, not_(empty_2_tmp))
raddr_next_2_tmp = add(raddr.O, uint(1, 2))
next_empty_next_2_tmp = eq(raddr_next_2_tmp, waddr.O)
next_full_next_2_tmp = bit(False)
wire(bits(raddr_next_2_tmp), raddr_next.I2)
wire(next_empty_next_2_tmp, next_empty_next.I2)
for __silica_i in range(4):
    wire(memory[__silica_i].O, memory_next[__silica_i].I2)
wire(next_full_next_2_tmp, next_full_next.I2)
wire(bits(waddr_next_2_tmp), waddr_next.I2)
wire(rdata_2_tmp, rdata.I2)
wire(full_2_tmp, full.I2)
wire(empty_2_tmp, empty.I2)
wire(__silica_path_state.I[2], and_(__silica_yield_state.O[0], __silica_cond_4, __silica_cond_5))
raddr_next_3_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_3_tmp = next_empty.O
next_full_next_3_tmp = next_full.O
waddr_next_3_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_3_tmp = next_full.O
empty_3_tmp = next_empty.O
rdata_3_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_6 = not_(and_(wen, not_(full_3_tmp)))
__silica_cond_7 = not_(and_(ren, not_(empty_3_tmp)))
wire(bits(raddr_next_3_tmp), raddr_next.I3)
wire(next_empty_next_3_tmp, next_empty_next.I3)
for __silica_i in range(4):
    wire(memory[__silica_i].O, memory_next[__silica_i].I3)
wire(next_full_next_3_tmp, next_full_next.I3)
wire(bits(waddr_next_3_tmp), waddr_next.I3)
wire(rdata_3_tmp, rdata.I3)
wire(full_3_tmp, full.I3)
wire(empty_3_tmp, empty.I3)
wire(__silica_path_state.I[3], and_(__silica_yield_state.O[0], __silica_cond_6, __silica_cond_7))
raddr_next_4_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_4_tmp = next_empty.O
next_full_next_4_tmp = next_full.O
waddr_next_4_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_4_tmp = next_full.O
empty_4_tmp = next_empty.O
rdata_4_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_8 = and_(wen, not_(full_4_tmp))
__silica_decoder_9 = decoder(waddr.O)
for i in range(len(memory)):
    memory_next_4_tmp[i] = DefineSilicaMux(2, len(mux([x.O for x in memory],
        i)))()(mux([x.O for x in memory], i), wdata, bits([not_(
        __silica_decoder_9[i]), __silica_decoder_9[i]]))
waddr_next_4_tmp = add(waddr.O, uint(1, 2))
next_full_next_4_tmp = eq(raddr.O, waddr_next_4_tmp)
next_empty_next_4_tmp = bit(False)
__silica_cond_9 = and_(ren, not_(empty_4_tmp))
raddr_next_4_tmp = add(raddr.O, uint(1, 2))
next_empty_next_4_tmp = eq(raddr_next_4_tmp, waddr_next_4_tmp)
next_full_next_4_tmp = bit(False)
wire(bits(raddr_next_4_tmp), raddr_next.I4)
wire(next_empty_next_4_tmp, next_empty_next.I4)
for __silica_i in range(4):
    wire(memory_next_4_tmp[__silica_i], memory_next[__silica_i].I4)
wire(next_full_next_4_tmp, next_full_next.I4)
wire(bits(waddr_next_4_tmp), waddr_next.I4)
wire(rdata_4_tmp, rdata.I4)
wire(full_4_tmp, full.I4)
wire(empty_4_tmp, empty.I4)
wire(__silica_path_state.I[4], and_(__silica_yield_state.O[1], __silica_cond_8, __silica_cond_9))
raddr_next_5_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_5_tmp = next_empty.O
next_full_next_5_tmp = next_full.O
waddr_next_5_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_5_tmp = next_full.O
empty_5_tmp = next_empty.O
rdata_5_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_10 = and_(wen, not_(full_5_tmp))
__silica_decoder_9 = decoder(waddr.O)
for i in range(len(memory)):
    memory_next_5_tmp[i] = DefineSilicaMux(2, len(mux([x.O for x in memory],
        i)))()(mux([x.O for x in memory], i), wdata, bits([not_(
        __silica_decoder_9[i]), __silica_decoder_9[i]]))
waddr_next_5_tmp = add(waddr.O, uint(1, 2))
next_full_next_5_tmp = eq(raddr.O, waddr_next_5_tmp)
next_empty_next_5_tmp = bit(False)
__silica_cond_11 = not_(and_(ren, not_(empty_5_tmp)))
wire(bits(raddr_next_5_tmp), raddr_next.I5)
wire(next_empty_next_5_tmp, next_empty_next.I5)
for __silica_i in range(4):
    wire(memory_next_5_tmp[__silica_i], memory_next[__silica_i].I5)
wire(next_full_next_5_tmp, next_full_next.I5)
wire(bits(waddr_next_5_tmp), waddr_next.I5)
wire(rdata_5_tmp, rdata.I5)
wire(full_5_tmp, full.I5)
wire(empty_5_tmp, empty.I5)
wire(__silica_path_state.I[5], and_(__silica_yield_state.O[1], __silica_cond_10, __silica_cond_11))
raddr_next_6_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_6_tmp = next_empty.O
next_full_next_6_tmp = next_full.O
waddr_next_6_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_6_tmp = next_full.O
empty_6_tmp = next_empty.O
rdata_6_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_12 = not_(and_(wen, not_(full_6_tmp)))
__silica_cond_13 = and_(ren, not_(empty_6_tmp))
raddr_next_6_tmp = add(raddr.O, uint(1, 2))
next_empty_next_6_tmp = eq(raddr_next_6_tmp, waddr.O)
next_full_next_6_tmp = bit(False)
wire(bits(raddr_next_6_tmp), raddr_next.I6)
wire(next_empty_next_6_tmp, next_empty_next.I6)
for __silica_i in range(4):
    wire(memory[__silica_i].O, memory_next[__silica_i].I6)
wire(next_full_next_6_tmp, next_full_next.I6)
wire(bits(waddr_next_6_tmp), waddr_next.I6)
wire(rdata_6_tmp, rdata.I6)
wire(full_6_tmp, full.I6)
wire(empty_6_tmp, empty.I6)
wire(__silica_path_state.I[6], and_(__silica_yield_state.O[1], __silica_cond_12, __silica_cond_13))
raddr_next_7_tmp = [raddr.O[__silica_i] for __silica_i in range(2)]
next_empty_next_7_tmp = next_empty.O
next_full_next_7_tmp = next_full.O
waddr_next_7_tmp = [waddr.O[__silica_i] for __silica_i in range(2)]
full_7_tmp = next_full.O
empty_7_tmp = next_empty.O
rdata_7_tmp = mux([x.O for x in memory], raddr.O)
__silica_cond_14 = not_(and_(wen, not_(full_7_tmp)))
__silica_cond_15 = not_(and_(ren, not_(empty_7_tmp)))
wire(bits(raddr_next_7_tmp), raddr_next.I7)
wire(next_empty_next_7_tmp, next_empty_next.I7)
for __silica_i in range(4):
    wire(memory[__silica_i].O, memory_next[__silica_i].I7)
wire(next_full_next_7_tmp, next_full_next.I7)
wire(bits(waddr_next_7_tmp), waddr_next.I7)
wire(rdata_7_tmp, rdata.I7)
wire(full_7_tmp, full.I7)
wire(empty_7_tmp, empty.I7)
wire(__silica_path_state.I[7], and_(__silica_yield_state.O[1], __silica_cond_14, __silica_cond_15))
EndDefine()