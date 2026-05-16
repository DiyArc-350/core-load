# 5G Core Load Reduction Analyzer

This lightweight, production-ready Python utility is designed to monitor and evaluate the impact of architectural optimizations (such as control plane caching, session pruning, or MEC local breakout) on a 5G Core Virtual Machine or Compute node. 

It calculates infrastructure stress alongside real-time Packets Per Second (PPS) and Throughput Data Rates, providing an instant analytical breakdown when stopped.

---

## Prerequisites

The tool uses Python 3 and relies on the native system-level library psutil to extract kernel and socket statistics.

1. Install Python 3 (if not already installed):
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip -y