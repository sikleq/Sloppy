"""A tiny client for the Source 2 remote console (VConsole2, TCP 127.0.0.1:29000) — to drive a running Dota 2
from a script: send console commands, read what the game prints.

Framing (big-endian): 4-byte type ("CMND", "PRNT", ...), uint32 version, uint16 total length incl. the 12-byte
header, uint16 handle; a CMND body is the command + NUL; a PRNT body carries its text from byte 28.
"""
import socket
import struct
import time

_HEADER = struct.Struct(">4sIHH")
_CMND_VERSION = 0x00D40000


class GameConsole:
    def __init__(self, host="127.0.0.1", port=29000, timeout=120.0):
        deadline = time.time() + timeout
        while True:
            try:
                self.sock = socket.create_connection((host, port), timeout=5)
                break
            except OSError:
                if time.time() > deadline:
                    raise
                time.sleep(2)
        self.sock.settimeout(0.2)
        self.buf = b""
        self.log = []

    def send(self, cmd):
        body = cmd.encode("utf-8") + b"\x00"
        self.sock.sendall(_HEADER.pack(b"CMND", _CMND_VERSION, _HEADER.size + len(body), 0) + body)

    def pump(self, seconds=0.5):
        """Read what the game printed for `seconds`; returns the new lines."""
        end, new = time.time() + seconds, []
        while time.time() < end:
            try:
                chunk = self.sock.recv(65536)
                if not chunk:
                    break
                self.buf += chunk
            except socket.timeout:
                pass
            while len(self.buf) >= _HEADER.size:
                kind, version, length, _ = _HEADER.unpack(self.buf[:_HEADER.size])
                if kind == b"CVRB":              # the cvar dump: too big for 16 bits, its 4 bytes after the type
                    length = version             # are the whole packet's length
                if length < _HEADER.size or len(self.buf) < length:
                    break
                body, self.buf = self.buf[_HEADER.size:length], self.buf[length:]
                if kind == b"PRNT" and len(body) > 28:
                    text = body[28:].split(b"\x00", 1)[0].decode("utf-8", "replace").rstrip()
                    if text:
                        new.append(text)
        self.log += new
        return new

    def run(self, cmd, wait=0.5):
        self.send(cmd)
        return self.pump(wait)

    def close(self):
        self.sock.close()
