# Week 4 · Task 1 observation

- **Protocol:** Stop-and-wait ARQ. Keeping only one chunk outstanding makes it straightforward to match ACKs to sequence numbers and retransmit after loss; stale ACKs cannot acknowledge a later chunk.
- **Packet count:** With seed 246, the data channel recorded 323 send attempts for 2,000 bytes. The minimum is 250 packets (2,000 / 8), so stop-and-wait used 1.29× the minimum, about 29% extra transmissions. The channel reported 40 lost packets and 8 duplicates.
- **Failure mode:** Loss dominated the default run and triggered retransmission; a lost ACK also causes the sender to retry the same sequence number. Reordering is handled by ordered buffering, and duplicate data is ACKed without being appended twice.

## Task 2 · Network measurement (2026-10-12, Asia/Seoul)

### Part A · Captured TCP handshake

- **A1:** Captured on this machine's Wi-Fi interface while `task2_measure.py` ran five HTTPS transfers. The submitted `out/tcp.pcapng` is privacy-filtered to one TCP stream whose TLS SNI is `speed.cloudflare.com`; other traffic to Cloudflare's shared IP was excluded.
- **A2:** In the submitted capture, packet **1** is the client SYN (`192.168.0.14:53336 → 172.66.0.218:443`), packet **2** is the server SYN-ACK, and packet **3** is the client's final ACK.
- **A3:** Initial sequence numbers from the packet headers are client **3,606,441,471** and server **2,146,773,082**. They are endpoint-chosen initial sequence numbers rather than zero; using distinct, hard-to-predict starting points helps prevent old segments from being mistaken for data in a new connection and makes blind injection harder. Wireshark's relative sequence-number display starts both at zero, so the reported values are the raw sequence numbers.
- **A4:** Client SYN (packet 1): MSS **1460 bytes**, window-scale shift **8** (factor 256), SACK permitted. Server SYN-ACK (packet 2): MSS **1400 bytes**, window-scale shift **13**, SACK permitted.
- **A5:** The client is the receiver for the download. Its later ACK advertises raw window **255** with the negotiated client scale factor **256**, so the scaled receive window is **65,280 bytes**. The largest Wireshark `tcp.analysis.bytes_in_flight` value in this stream is **62,780 bytes** (packet **3213**), leaving **2,500 bytes** of advertised space unused. The receiver window was not quite full; the sender's congestion window or available path capacity, rather than the advertised receive-window ceiling, was the likely limit. The capture does not expose the sender's congestion window directly.

### Part B · Throughput

- **Current network:** Five 5 MB HTTPS transfers measured a median of **58.81 Mbps**, from **52.08 to 68.43 Mbps** (16.35 Mbps range; **27.8%** of the median). Median TCP handshake time was **10.9 ms**.
- **Phone tethering:** Five transfers measured a median of **24.41 Mbps**, from **21.75 to 38.26 Mbps** (16.51 Mbps range; **67.6%** of the median). Median TCP handshake time was **56.0 ms**.
- **Capture-time sample:** The five transfers made while capturing measured a median of **64.26 Mbps**, from **34.76 to 69.98 Mbps** (35.22 Mbps range; **54.8%** of the median). Median TCP handshake time was **12.1 ms**. This extra sample is kept separately because its network label was not identified.
- **B1–B5:** The two named networks each have five runs. Tethering's median was about **58.5% lower** than the current network's, while its median handshake was about **45.1 ms longer** (about **5.1×**). The finite transfers are consistent with TCP slow start: a longer RTT delays congestion-window growth over each round trip, which can reduce delivered throughput. The measurements do not isolate RTT from link capacity, radio conditions, server load, or path variation. Spread across runs may reflect changing wireless conditions and network/server load; these are possible causes, not directly measured causes. The two-network comparison shows an association, not proof that handshake delay alone caused the throughput difference.
