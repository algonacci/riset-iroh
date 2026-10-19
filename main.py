
import argparse
import asyncio

import iroh

ALPN = b"iroh-ffi/example/0"


async def accept(ep):
    print("Node ID:", ep.id())

    ticket = iroh.EndpointTicket.from_addr(ep.addr())
    print("\nSHARE THIS TICKET WITH THE CLIENT:\n")
    print(ticket)
    print("\nWaiting for connection...")

    incoming = await ep.accept_next()
    if incoming is None:
        return

    accepting = await incoming.accept()
    conn = await accepting.connect()

    print("Connected to:", conn.remote_id())

    bi = await conn.accept_bi()
    recv = bi.recv()
    send = bi.send()

    data = await recv.read_to_end(4096)
    message = data.decode("utf-8")

    print("Received:", message)

    response = f"Echo from Iroh node: {message}"
    await send.write_all(response.encode("utf-8"))
    await send.finish()

    await asyncio.sleep(0.5)
    await ep.close()


async def connect(ep, ticket_string):
    ticket = iroh.EndpointTicket.from_string(ticket_string)
    addr = ticket.endpoint_addr()

    print("Connecting to:", addr.id())

    conn = await ep.connect(addr, ALPN)
    bi = await conn.open_bi()

    send = bi.send()
    recv = bi.recv()

    await send.write_all(b"Hello from Python!")
    await send.finish()

    response = await recv.read_to_end(4096)
    print("Server replied:", response.decode("utf-8"))

    await ep.close()


async def main():
    iroh.iroh_ffi.uniffi_set_event_loop(
        asyncio.get_running_loop()
    )

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("accept")

    client = sub.add_parser("connect")
    client.add_argument("ticket")

    args = parser.parse_args()

    alpns = [ALPN] if args.cmd == "accept" else None
    options = iroh.EndpointOptions(alpns=alpns)

    ep = await iroh.Endpoint.bind(options)

    if args.cmd == "accept":
        await accept(ep)
    else:
        await connect(ep, args.ticket)


if __name__ == "__main__":
    asyncio.run(main())

