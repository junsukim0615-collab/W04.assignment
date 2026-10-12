#!/usr/bin/env python3
"""Week 4 · Task 1 — reliable delivery over an unreliable channel.

Implements stop-and-wait ARQ: each numbered payload is sent until its matching
ACK arrives. The receiver buffers by sequence number and only exposes bytes in
order; duplicate packets are acknowledged but never appended twice.
"""
import argparse
import hashlib
import random

PAYLOAD = 8
TIMEOUT = 8


class UnreliableChannel:
    """Loses 10%, duplicates 3%, reorders, and delays. Deterministic by seed."""

    def __init__(self, seed=246, loss=0.10, dup=0.03, reorder=0.10):
        self.rng = random.Random(seed)
        self.loss, self.dup, self.reorder = loss, dup, reorder
        self.wire = []
        self.stats = {"sent": 0, "lost": 0, "duplicated": 0, "delivered": 0}

    def send(self, packet):
        self.stats["sent"] += 1
        if self.rng.random() < self.loss:
            self.stats["lost"] += 1
            return
        copies = 2 if self.rng.random() < self.dup else 1
        self.stats["duplicated"] += copies - 1
        for _ in range(copies):
            if self.rng.random() < self.reorder and self.wire:
                self.wire.insert(self.rng.randrange(len(self.wire)), packet)
            else:
                self.wire.append(packet)

    def receive(self):
        if not self.wire:
            return None
        self.stats["delivered"] += 1
        return self.wire.pop(0)


class Sender:
    """Stop-and-wait sender with sequence-numbered chunks and a retry timer."""

    def __init__(self, data_channel, ack_channel, data):
        self.data_channel = data_channel
        self.ack_channel = ack_channel
        self.chunks = [data[i:i + PAYLOAD] for i in range(0, len(data), PAYLOAD)]
        self.next_seq = 0
        self.waiting = False
        self.elapsed = 0

    def step(self):
        if self.next_seq >= len(self.chunks):
            return False

        ack = self.ack_channel.receive()
        if ack == ("ACK", self.next_seq) and self.waiting:
            self.next_seq += 1
            self.waiting = False
            self.elapsed = 0
            if self.next_seq >= len(self.chunks):
                return False

        if not self.waiting:
            self.data_channel.send(("DATA", self.next_seq, self.chunks[self.next_seq]))
            self.waiting = True
            self.elapsed = 0
        else:
            self.elapsed += 1
            if self.elapsed >= TIMEOUT:
                self.data_channel.send(("DATA", self.next_seq, self.chunks[self.next_seq]))
                self.elapsed = 0
        return True


class Receiver:
    """In-order receiver that re-ACKs duplicates without appending them twice."""

    def __init__(self, data_channel, ack_channel):
        self.data_channel = data_channel
        self.ack_channel = ack_channel
        self.expected = 0
        self.buffer = {}
        self.parts = []

    def step(self):
        packet = self.data_channel.receive()
        if not (isinstance(packet, tuple) and len(packet) == 3 and packet[0] == "DATA"):
            return

        _, seq, payload = packet
        if not isinstance(seq, int) or seq < 0 or not isinstance(payload, bytes):
            return
        if seq >= self.expected:
            self.buffer.setdefault(seq, payload)
        while self.expected in self.buffer:
            self.parts.append(self.buffer.pop(self.expected))
            self.expected += 1

        # A duplicate of an already-delivered chunk gets the same ACK again.
        self.ack_channel.send(("ACK", seq))

    def data(self):
        return b"".join(self.parts)


def verify(seed=246, size=2000, max_steps=200_000):
    original = bytes(random.Random(seed).getrandbits(8) for _ in range(size))
    up, down = UnreliableChannel(seed), UnreliableChannel(seed + 1)
    sender = Sender(up, down, original)
    receiver = Receiver(up, down)

    for _ in range(max_steps):
        alive = sender.step()
        receiver.step()
        if not alive and len(receiver.data()) >= size:
            break

    got = receiver.data()
    ok = hashlib.sha256(got).hexdigest() == hashlib.sha256(original).hexdigest()
    print(f"  bytes    sent {size}   received {len(got)}")
    print(f"  channel  {up.stats}")
    print(f"  result   {'IDENTICAL' if ok else 'CORRUPTED OR INCOMPLETE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    p.add_argument("--seed", type=int, default=246)
    a = p.parse_args()
    raise SystemExit(verify(a.seed) if a.verify else p.print_help())
