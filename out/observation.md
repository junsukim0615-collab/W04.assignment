# Week 4 · Task 1 observation

- **Protocol:** Stop-and-wait ARQ. Keeping only one chunk outstanding makes it straightforward to match ACKs to sequence numbers and retransmit after loss; stale ACKs cannot acknowledge a later chunk.
- **Packet count:** With seed 246, the data channel recorded 323 send attempts for 2,000 bytes. The minimum is 250 packets (2,000 / 8), so stop-and-wait used 1.29× the minimum, about 29% extra transmissions. The channel reported 40 lost packets and 8 duplicates.
- **Failure mode:** Loss dominated the default run and triggered retransmission; a lost ACK also causes the sender to retry the same sequence number. Reordering is handled by ordered buffering, and duplicate data is ACKed without being appended twice.

## Task 2 · Network measurement (2026-10-12, Asia/Seoul)

- **Part A status:** A local packet trace is not yet available. Wireshark and tshark are absent, and Windows PktMon denied access to its capture driver. Therefore A2–A5 (packet numbers, initial sequence numbers, SYN options, scaled receive window, and in-flight bytes) still need answers from a capture or the official 9th-edition TCP trace. No packet values are inferred or fabricated.
- **Part B, current network:** Five 5 MB HTTPS transfers to Cloudflare measured a median of **58.81 Mbps**, from **52.08 to 68.43 Mbps** (16.35 Mbps range; 28% of the median). Median TCP handshake time was **10.9 ms**.
- **Part B, phone tethering:** Five 5 MB transfers measured a median of **24.41 Mbps**, from **21.75 to 38.26 Mbps** (16.51 Mbps range; 68% of the median). Median TCP handshake time was **56.0 ms**.
- **B1–B5 comparison:** Both network labels have five runs. The tethering median throughput was about **58.5% lower**, while its median handshake was about **45.1 ms longer** (about 5.1×). Higher RTT can delay TCP's congestion-window growth during a finite transfer (slow start), which is consistent with the lower observed throughput. These measurements do not isolate RTT from link capacity, radio conditions, server load, or path variation. The larger tethering spread may reflect variable wireless conditions or load; this is a hypothesis, not a measured cause. The data show an association between longer handshake time and lower throughput in these two samples, not proof that handshake delay caused the throughput difference.
