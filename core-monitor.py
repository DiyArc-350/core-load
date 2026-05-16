import time
import sys
import psutil

def format_bytes(bytes_num):
    """Converts bytes to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unit}"
        bytes_num /= 1024.0

class CoreLoadAnalyzer:
    def __init__(self, interval=2):
        self.interval = interval
        self.cpu_log = []
        self.mem_log = []
        self.start_time = None
        
        # Network tracking for UPF / SBI throughput analysis
        self.net_start = None
        self.net_prev = None

    def start_monitoring(self):
        print("=" * 70)
        print(" 5G CORE LOAD REDUCTION ANALYZER INITIALIZED ")
        print(" Monitoring core infrastructure, PPS, and throughput baselines...")
        print(" Press Ctrl+C to stop the traffic test and generate the summary.")
        print("=" * 70)
        
        self.start_time = time.time()
        self.net_start = psutil.net_io_counters()
        self.net_prev = self.net_start
        
        try:
            while True:
                # 1. Gather Metrics
                cpu_p = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                net_now = psutil.net_io_counters()
                
                # Record metrics for historical calculation
                self.cpu_log.append(cpu_p)
                self.mem_log.append(mem.percent)
                
                # Calculate Delta metrics for the specific interval window
                bytes_sent_delta = net_now.bytes_sent - self.net_prev.bytes_sent
                bytes_recv_delta = net_now.bytes_recv - self.net_prev.bytes_recv
                pkts_sent_delta = net_now.packets_sent - self.net_prev.packets_sent
                pkts_recv_delta = net_now.packets_recv - self.net_prev.packets_recv
                
                # Convert deltas to rates per second
                pps_tx = pkts_sent_delta / self.interval
                pps_rx = pkts_recv_delta / self.interval
                bps_tx = bytes_sent_delta / self.interval
                bps_rx = bytes_recv_delta / self.interval
                
                # Update previous step network placeholder
                self.net_prev = net_now
                
                # 2. Output Live Ticker
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] CPU: {cpu_p:5.1f}% | RAM: {mem.percent:5.1f}% | "
                      f"Tx Rate: {format_bytes(bps_tx)}/s ({int(pps_tx)} PPS) | "
                      f"Rx Rate: {format_bytes(bps_rx)}/s ({int(pps_rx)} PPS)")
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.generate_summary_report()

    def generate_summary_report(self):
        end_time = time.time()
        duration = end_time - self.start_time
        net_end = psutil.net_io_counters()
        
        # Calculate totals over the entire window
        total_tx_bytes = net_end.bytes_sent - self.net_start.bytes_sent
        total_rx_bytes = net_end.bytes_recv - self.net_start.bytes_recv
        total_tx_pkts = net_end.packets_sent - self.net_start.packets_sent
        total_rx_pkts = net_end.packets_recv - self.net_start.packets_recv
        
        # Security check if terminated instantly
        if not self.cpu_log:
            print("\n[Error] Not enough data points captured.")
            return
            
        avg_cpu = sum(self.cpu_log) / len(self.cpu_log)
        max_cpu = max(self.cpu_log)
        avg_mem = sum(self.mem_log) / len(self.mem_log)
        max_mem = max(self.mem_log)
        
        avg_pps_tx = total_tx_pkts / duration if duration > 0 else 0
        avg_pps_rx = total_rx_pkts / duration if duration > 0 else 0
        avg_bps_tx = total_tx_bytes / duration if duration > 0 else 0
        avg_bps_rx = total_rx_bytes / duration if duration > 0 else 0

        # --- Report Layout ---
        print("\n" + "=" * 70)
        print("                   5G CORE LOAD ANALYSIS REPORT                    ")
        print("=" * 70)
        print(f"Test Execution Duration : {duration:.2f} seconds")
        print("-" * 70)
        print(f"{'Core Parameter Group':<24} | {'Average Metrics':<20} | {'Peak Performance':<20}")
        print("-" * 70)
        print(f"{'[Compute] CPU Capacity':<24} | {avg_cpu:.2f}%" + f" {' ' * 13} | {max_cpu:.2f}%")
        print(f"{'[Compute] Memory Load':<24} | {avg_mem:.2f}%" + f" {' ' * 13} | {max_mem:.2f}%")
        print(f"{'[UPF/SBI] Outbound (Tx)':<24} | {format_bytes(avg_bps_tx)}/s" + f" {' ' * 8} | {int(avg_pps_tx)} PPS (Avg)")
        print(f"{'[UPF/SBI] Inbound (Rx)':<24} | {format_bytes(avg_bps_rx)}/s" + f" {' ' * 8} | {int(avg_pps_rx)} PPS (Avg)")
        print("-" * 70)
        print(f"Total Network Footprint  | Tx Volume: {format_bytes(total_tx_bytes)} | Rx Volume: {format_bytes(total_rx_bytes)}")
        print("=" * 70)
        
        # --- Analytics Insight for Optimization Verification ---
        print("\nLOAD REDUCTION INSIGHTS FOR ENGINEER REVIEW:")
        print(f" - Packet Processing Overhead: Total packets handled = {total_tx_pkts + total_rx_pkts} frames.")
        print(f" - Control vs User Plane Balance: Your peak compute load was {max_cpu:.1f}%.")
        print(" - To verify Load Reduction: Compare the Averages/Peaks above against your unmodified baseline test.")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    analyzer = CoreLoadAnalyzer(interval=2)
    analyzer.start_monitoring()