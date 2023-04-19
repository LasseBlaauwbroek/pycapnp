#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
import ssl
import socket

import capnp
import thread_capnp


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

this_dir = os.path.dirname(os.path.abspath(__file__))


class ExampleImpl(thread_capnp.Example.Server):
    "Implementation of the Example threading Cap'n Proto interface."

    def subscribeStatus(self, subscriber, **kwargs):
        return (
            capnp.getTimer()
            .after_delay(10**9)
            .then(lambda: subscriber.status(True))
            .then(lambda _: self.subscribeStatus(subscriber))
        )

    def longRunning(self, **kwargs):
        return capnp.getTimer().after_delay(1 * 10**9)

    def alive(self, **kwargs):
        return True


async def new_connection(stream):
    server = capnp.TwoPartyServer(stream, bootstrap=ExampleImpl())
    await server.on_disconnect()


def parse_args():
    parser = argparse.ArgumentParser(
        usage="""Runs the server bound to the given address/port ADDRESS. """
    )
    parser.add_argument("address", help="ADDRESS:PORT")
    return parser.parse_args()


async def main():
    host, port = parse_args().address.split(":")

    # Setup SSL context
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(
        os.path.join(this_dir, "selfsigned.cert"),
        os.path.join(this_dir, "selfsigned.key"),
    )

    # Handle both IPv4 and IPv6 cases
    try:
        print("Try IPv4")
        server = await capnp.AsyncIoStream.create_server(
            new_connection, host, port, ssl=ctx, family=socket.AF_INET
        )
    except Exception:
        print("Try IPv6")
        server = await capnp.AsyncIoStream.create_server(
            new_connection, host, port, ssl=ctx, family=socket.AF_INET6
        )

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
