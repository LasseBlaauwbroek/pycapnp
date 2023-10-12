import os
import socket
import sys  # add examples dir to sys.path
import pytest

import capnp

examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
sys.path.append(examples_dir)

import async_calculator_server  # noqa: E402
import calculator_capnp


@pytest.fixture(autouse=True)
async def kj_loop():
    async with capnp.kj_loop():
        yield


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

    _ = capnp.TwoPartyServer(write, bootstrap=async_calculator_server.CalculatorImpl())
    await main(read)
