# TCP Heartbeat Client-Server

This project implements a simple TCP client-server system in Python where:

- The **client** sends periodic heartbeat messages with a sequence number and timestamp.
- The **server** receives and logs these heartbeats, and analyzes them for delay and missed messages.

