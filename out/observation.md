# Week 4 · Task 1 observation

- **Protocol:** Stop-and-wait ARQ. Keeping only one chunk outstanding makes it straightforward to match ACKs to sequence numbers and retransmit after loss; stale ACKs cannot acknowledge a later chunk.
- **Packet count:** With seed 246, the data channel recorded 323 send attempts for 2,000 bytes. The minimum is 250 packets (2,000 / 8), so stop-and-wait used 1.29× the minimum, about 29% extra transmissions. The channel reported 40 lost packets and 8 duplicates.
- **Failure mode:** Loss dominated the default run and triggered retransmission; a lost ACK also causes the sender to retry the same sequence number. Reordering is handled by ordered buffering, and duplicate data is ACKed without being appended twice.
