from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
import time
import json
import subprocess


def read_interface(interfaces):
    total_byte = 0
    total_packet = 0
    with open("/proc/net/dev", encoding='utf8') as f:
        for row in f.readlines():
            for iface in interfaces:
                if row.startswith("%s:" % iface):
                    iface, byte, packet, rest = row.split(None, 3)
                    total_byte += int(byte)
                    total_packet += int(packet)
    return total_byte, total_packet


def read_interface_ethtool(interfaces):
    total_byte = 0
    total_packet = 0
    for iface in interfaces:
        p = subprocess.Popen(["/usr/sbin/ethtool", "-S", iface], stdout=subprocess.PIPE)
        (stdout, stderr) = p.communicate()
        for row in stdout.decode("utf-8").splitlines():
            if row.strip().startswith("rx_bytes_nic:"):
                byte = row.strip().split(":")[1].strip()
                total_byte += int(byte)
    return total_byte, total_packet



class Handler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET")
        self.send_header("Access-Control-Allow-Headers", " X-Custom-Header")
        self.end_headers();
        self.wfile.write(b"")


    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache", "no-store")
        self.end_headers()
        interfaces = self.path.strip("/").split(",")
        byte, packet = read_interface_ethtool(interfaces)
        while True:
            byte_new, packet_new = read_interface_ethtool(["enp6s0f0", "enp6s0f1"])
            self.wfile.write(b'data: ' + json.dumps({"bps": (byte_new-byte)/0.1*8, "pps": (packet_new-packet)/0.1}).encode("utf-8") + b'\n\n')
            byte = byte_new
            packet = packet_new
            time.sleep(0.1)


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass

def run():
    server = ThreadingSimpleServer(('0.0.0.0', 4444), Handler)
    server.serve_forever()


if __name__ == '__main__':
    run()
