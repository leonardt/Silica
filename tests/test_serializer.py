from silica import coroutine, uint, Bit, BitVector, compile, Array, Bits, bits
from magma.testing.coroutine import check


@coroutine(inputs={"I" : Array(4, Bits(16))})
def Serializer4():
    data = [bits(0, 16) for _ in range(3)]
    I = yield
    while True:
        O = I[0]
        # data = I[1:]
        for i in range(3):
            data[i] = I[i + 1]
        I = yield O
        for i in range(3):
            O = data[i]
            I = yield O


@coroutine
def inputs_generator(inputs):
    while True:
        for i in inputs:
            I = [BitVector(x, 16) for x in i]
            yield I
            for _ in range(3):
                I = [BitVector((_ * len(i)) + j, 16) for j in range(len(i))]
                yield I

def test_ser3():
    ser = Serializer4()
    inputs = [[4,5,6,7],[10,16,8,3]]
    for I in inputs:
      ser.send(I)
      for i in range(3):
        assert ser.O == I[i]
        next(ser)

    serializer4 = compile(ser, "serializer4_magma.py")
    print(repr(serializer4))
    check(serializer4, Serializer4(), 9, inputs_generator(inputs))
