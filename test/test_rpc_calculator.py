import os
import socket
import sys  # add examples dir to sys.path
import pytest

import capnp

examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
sys.path.append(examples_dir)

import calculator_capnp


@pytest.fixture(autouse=True)
async def kj_loop():
    async with capnp.kj_loop():
        yield


async def evaluate_impl(expression, params=None):
    which = expression.which()

    if which == "literal":
        return expression.literal
    else:
        raise Exception("bla")


class ValueImpl(calculator_capnp.Calculator.Value.Server):
    def __init__(self, value):
        self.value = value

    async def read(self, **kwargs):
        return self.value


class CalculatorImpl(calculator_capnp.Calculator.Server):
    async def evaluate(self, expression, _context, **kwargs):
        return ValueImpl(await evaluate_impl(expression))


async def main(connection):
    client = capnp.TwoPartyClient(connection)

    # Bootstrap the Calculator interface
    calculator = client.bootstrap().cast_as(calculator_capnp.Calculator)
    eval_promise = calculator.evaluate({"literal": 123})
    read_promise = eval_promise.value.read()
    response = await read_promise
    assert response.value == 123

    print("PASS")


async def test_calculator():
    read, write = socket.socketpair()
    read = await capnp.AsyncIoStream.create_connection(sock=read)
    write = await capnp.AsyncIoStream.create_connection(sock=write)

    _ = capnp.TwoPartyServer(write, bootstrap=CalculatorImpl())
    await main(read)
