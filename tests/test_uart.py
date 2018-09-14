import magma as m
m.set_mantle_target("ice40")
import mantle
import silica
from silica import bit, bits
import fault
from common import evaluate_circuit

# @silica.coroutine
# def uart_transmitter(data : In(Array(8, Bit)), valid : In(Bit), 
#                      tx : Out(Bit)):
#     while True:
#         if valid:
#             tx = 0  # start bit
#             yield
#             for i in range(0, 8):
#                 tx = data[i]
#                 yield
#             tx = 1  # end bit
#             yield
#         else:
#             tx = 1
#             yield

@silica.coroutine(inputs={"data": silica.Bits(8), "valid": silica.Bit})
def uart_transmitter():
    message = bits(0, 8)
    data, valid = yield
    while True:
        if valid:
            message = data
            tx = bit(0)  # start bit
            ready = bit(0)
            data, valid = yield tx, ready
            for i in range(7, -1, -1):
                tx = message[i]
                ready = bit(0)
                data, valid = yield tx, ready
            tx = bit(1)  # end bit
            ready = bit(0)
            data, valid = yield tx, ready
        else:
            tx = bit(1)
            ready = bit(1)
            data, valid = yield tx, ready

        # Interestingly enough, this variant produces worse quality
            # ready = bit(0)
        # else:
            # ready = bit(1)
        # tx = bit(1)
        # data, valid = yield tx, ready


def test_UART():
    uart = uart_transmitter()
    si_uart = silica.compile(uart, "tests/build/uart.v")
    tester = fault.Tester(si_uart, si_uart.CLK)
    tester.step(2)
    for message in [0xDE, 0xAD]:
        tester.expect(si_uart.ready, 1)
        tester.poke(si_uart.data, message)
        tester.poke(si_uart.valid, 1)
        tester.step(2)
        tester.poke(si_uart.data, 0xFF)
        tester.poke(si_uart.valid, 0)
        tester.expect(si_uart.ready, 0)

        # start bit
        tester.expect(si_uart.tx, 0)
        for i in range(8):
            tester.step(2)
            tester.expect(si_uart.tx, (message >> (7-i)) & 1)
        tester.step(2)
        # end bit
        tester.expect(si_uart.tx, 1)
        tester.step(2)
        tester.expect(si_uart.ready, 1)
        tester.eval()

    tester.compile_and_run(target="verilator", directory="tests/build",
                           flags=['-Wno-fatal'])
    verilog_uart = m.DefineFromVerilogFile(
        'verilog/uart.v', type_map={'CLK': m.In(m.Clock)})[0]
    verilog_tester = tester.retarget(verilog_uart, verilog_uart.CLK)

    verilog_tester.compile_and_run(target="verilator", directory="tests/build",
                                   flags=['-Wno-fatal'])
    if __name__ == '__main__':
        print("===== BEGIN : SILICA RESULTS =====")
        evaluate_circuit("uart", "uart_transmitter")
        print("===== END   : SILICA RESULTS =====")
        import shutil
        shutil.copy('verilog/uart.v', 'tests/build/verilog_uart.v')
        print("===== BEGIN : MAGMA RESULTS =====")
        evaluate_circuit("verilog_uart", "uart_tx")
        print("===== END   : MAGMA RESULTS =====")

if __name__ == '__main__':
    test_UART()