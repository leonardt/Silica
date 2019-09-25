import pytest
import fault
import silica as si
from silica import bits, uint, memory, bit
import shutil
import pytest
from hwtypes import BitVector
import magma as m


@si.coroutine
def SilicaFifo(wdata: si.Bits[4], wen: si.Bit, ren: si.Bit) -> \
        {"rdata": si.Bits[4], "empty": si.Bit, "full": si.Bit}:
    buffer = memory(4, 4)
    raddr = uint(0, 3)
    waddr = uint(0, 3)
    wdata, wen, ren = yield
    while True:
        full = (waddr[:2] == raddr[:2]) & (waddr[2] != raddr[2])
        empty = waddr == raddr
        rdata = buffer[raddr[:2]]
        w_valid = wen & ~full
        r_valid = ren & ~empty
        if w_valid:
            buffer[waddr[:2]] = wdata
            waddr = waddr + uint(1, 3)
        if r_valid:
            raddr = raddr + uint(1, 3)
        wdata, wen, ren = yield rdata, empty, full

    # buffer = memory(4, 4)
    # raddr = uint(0, 3)
    # waddr = uint(0, 3)
    # while True:
    #     empty = waddr == raddr
    #     full = (waddr[:2] == raddr[:2]) & (waddr[2] != raddr[2])
    #     rdata = buffer[raddr[:2]]
    #     wdata, wen, ren = yield rdata, empty, full
    #     if wen and not full:
    #         buffer[waddr[:2]] = wdata
    #         waddr = waddr + 1
    #     if ren and not empty:
    #         raddr = raddr + 1

expected_trace = [
    # Old trace without bit packing
    # {'wdata': 1, 'wen': 0, 'ren': 1, 'rdata': 0, 'full': False, 'empty':
    # True, 'buffer': [0, 0, 0, 0], 'raddr': 0, 'waddr': 0},
    # {'wdata': 2, 'wen': 1, 'ren': 0, 'rdata': 2, 'full': False, 'empty':
    # False, 'buffer': [2, 0, 0, 0], 'raddr': 0, 'waddr': 1},
    # {'wdata': 3, 'wen': 1, 'ren': 1, 'rdata': 3, 'full': False, 'empty':
    # False, 'buffer': [2, 3, 0, 0], 'raddr': 1, 'waddr': 2},
    # {'wdata': 4, 'wen': 1, 'ren': 0, 'rdata': 3, 'full': False, 'empty':
    # False, 'buffer': [2, 3, 4, 0], 'raddr': 1, 'waddr': 3},
    # {'wdata': 5, 'wen': 0, 'ren': 1, 'rdata': 4, 'full': False, 'empty':
    # False, 'buffer': [2, 3, 4, 0], 'raddr': 2, 'waddr': 3},
    # {'wdata': 6, 'wen': 0, 'ren': 1, 'rdata': 0, 'full': False, 'empty':
    # True, 'buffer': [2, 3, 4, 0], 'raddr': 3, 'waddr': 3},
    # {'wdata': 7, 'wen': 1, 'ren': 0, 'rdata': 7, 'full': False, 'empty':
    # False, 'buffer': [2, 3, 4, 7], 'raddr': 3, 'waddr': 0},
    # {'wdata': 8, 'wen': 0, 'ren': 1, 'rdata': 2, 'full': False, 'empty':
    # True, 'buffer': [2, 3, 4, 7], 'raddr': 0, 'waddr': 0},
    # {'wdata': 9, 'wen': 1, 'ren': 1, 'rdata': 9, 'full': False, 'empty':
    # False, 'buffer': [9, 3, 4, 7], 'raddr': 0, 'waddr': 1},
    # {'wdata': 10, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': False, 'empty':
    # False, 'buffer': [9, 10, 4, 7], 'raddr': 0, 'waddr': 2},
    # {'wdata': 11, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': False, 'empty':
    # False, 'buffer': [9, 10, 11, 7], 'raddr': 0, 'waddr': 3},
    # {'wdata': 12, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': True, 'empty':
    # False, 'buffer': [9, 10, 11, 12], 'raddr': 0, 'waddr': 0},
    # {'wdata': 13, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': True, 'empty':
    # False, 'buffer': [9, 10, 11, 12], 'raddr': 0, 'waddr': 0},
    # {'wdata': 13, 'wen': 0, 'ren': 1, 'rdata': 10, 'full': False, 'empty':
    # False, 'buffer': [9, 10, 11, 12], 'raddr': 1, 'waddr': 0},
    # {'wdata': 14, 'wen': 1, 'ren': 1, 'rdata': 11, 'full': False, 'empty':
    # False, 'buffer': [14, 10, 11, 12], 'raddr': 2, 'waddr': 1},
    {'wdata': 1, 'wen': 0, 'ren': 1, 'rdata': 0, 'full': False, 'empty': True,
     'buffer': [0, 0, 0, 0], 'raddr': 0, 'waddr': 0},
    {'wdata': 2, 'wen': 1, 'ren': 0, 'rdata': 0, 'full': False, 'empty': True,
     'buffer': [2, 0, 0, 0], 'raddr': 0, 'waddr': 1},
    {'wdata': 3, 'wen': 1, 'ren': 1, 'rdata': 2, 'full': False, 'empty': False,
     'buffer': [2, 3, 0, 0], 'raddr': 1, 'waddr': 2},
    {'wdata': 4, 'wen': 1, 'ren': 0, 'rdata': 3, 'full': False, 'empty': False,
     'buffer': [2, 3, 4, 0], 'raddr': 1, 'waddr': 3},
    {'wdata': 5, 'wen': 0, 'ren': 1, 'rdata': 3, 'full': False, 'empty': False,
     'buffer': [2, 3, 4, 0], 'raddr': 2, 'waddr': 3},
    {'wdata': 6, 'wen': 0, 'ren': 1, 'rdata': 4, 'full': False, 'empty': False,
     'buffer': [2, 3, 4, 0], 'raddr': 3, 'waddr': 3},
    {'wdata': 7, 'wen': 1, 'ren': 0, 'rdata': 0, 'full': False, 'empty': True,
     'buffer': [2, 3, 4, 7], 'raddr': 3, 'waddr': 4},
    {'wdata': 8, 'wen': 0, 'ren': 1, 'rdata': 7, 'full': False, 'empty': False,
     'buffer': [2, 3, 4, 7], 'raddr': 4, 'waddr': 4},
    {'wdata': 9, 'wen': 1, 'ren': 1, 'rdata': 2, 'full': False, 'empty': True,
     'buffer': [9, 3, 4, 7], 'raddr': 4, 'waddr': 5},
    {'wdata': 10, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': False, 'empty':
     False, 'buffer': [9, 10, 4, 7], 'raddr': 4, 'waddr': 6},
    {'wdata': 11, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': False, 'empty':
     False, 'buffer': [9, 10, 11, 7], 'raddr': 4, 'waddr': 7},
    {'wdata': 12, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': False, 'empty':
     False, 'buffer': [9, 10, 11, 12], 'raddr': 4, 'waddr': 0},
    {'wdata': 13, 'wen': 1, 'ren': 0, 'rdata': 9, 'full': True, 'empty': False,
     'buffer': [9, 10, 11, 12], 'raddr': 4, 'waddr': 0},
    {'wdata': 13, 'wen': 0, 'ren': 1, 'rdata': 9, 'full': True, 'empty': False,
     'buffer': [9, 10, 11, 12], 'raddr': 5, 'waddr': 0},
    {'wdata': 14, 'wen': 1, 'ren': 1, 'rdata': 10, 'full': False, 'empty':
     False, 'buffer': [14, 10, 11, 12], 'raddr': 6, 'waddr': 1},
]


def inputs_generator(N):
    @si.coroutine
    def gen():
        while True:
            for trace in expected_trace:
                wdata = bits(trace["wdata"], N)
                wen = bool(trace["wen"])
                ren = bool(trace["ren"])
                yield wdata, wen, ren
    return gen()


@pytest.mark.parametrize("strategy", ["by_path", "by_statement"])
def test_fifo(strategy):
    fifo = SilicaFifo()
    si_fifo = si.compile(fifo, file_name="tests/build/si_fifo.v",
                         strategy=strategy)
    # si_fifo = m.DefineFromVerilogFile("tests/build/si_fifo.v",
    #                             type_map={"CLK": m.In(m.Clock)})[0]

    inputs = ("wdata", "wen", "ren")
    outputs = ("full", "empty", "rdata")
    states = ("buffer", "raddr", "waddr")
    tester = fault.Tester(si_fifo, si_fifo.CLK)
    for i, trace in enumerate(expected_trace):
        args = ()
        for input_ in inputs:
            args += (BitVector(trace[input_]), )
            tester.poke(si_fifo.interface.ports[input_], trace[input_])
            # tester.print(si_fifo.interface.ports[input_])
        fifo.send(args)
        tester.eval()
        for output in outputs:
            assert getattr(fifo, output) == trace[output], \
                (i, output, getattr(fifo, output), trace[output])
            tester.expect(si_fifo.interface.ports[output], trace[output])
            # tester.print(si_fifo.interface.ports[output])
        tester.step(2)
        for state in states:
            assert getattr(fifo, state) == trace[state], \
                (i, state, getattr(fifo, state), trace[state])

    tester.compile_and_run(target="verilator", directory="tests/build",
                           flags=['-Wno-fatal'], magma_output="verilog")
    verilog_fifo = m.DefineFromVerilogFile(
        "verilog/fifo.v", type_map={"CLK": m.In(m.Clock)})[0]

    verilog_tester = tester.retarget(verilog_fifo, verilog_fifo.CLK)
    verilog_tester.compile_and_run(target="verilator", directory="tests/build",
                                   flags=['-Wno-fatal'],
                                   include_directories=["../../verilog"],
                                   magma_output="verilog")
    if __name__ == '__main__':
        from tests.common import evaluate_circuit
        print("===== BEGIN : SILICA RESULTS =====")
        evaluate_circuit("si_fifo", "SilicaFifo")
        print("===== END   : SILICA RESULTS =====")
        import shutil
        shutil.copy("verilog/fifo.v", "tests/build")
        print("===== BEGIN : VERILOG RESULTS =====")
        evaluate_circuit("fifo", "fifo")
        print("===== END   : VERILOG RESULTS =====")


if __name__ == "__main__":
    import sys
    test_fifo(sys.argv[1])
