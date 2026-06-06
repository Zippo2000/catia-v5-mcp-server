#!/usr/bin/env python3
"""Create a donut (torus) in CATIA via MCP SSE — uses same transport as run_realtests.py."""
import json, re, sys, threading, time, uuid
import requests, sseclient

SSE_URL = "http://192.168.177.151:8765/sse"
MSG_URL = "http://192.168.177.151:8765/messages/"


class MCPSession:
    def __init__(self):
        self.session_id = None
        self._pending = {}
        self._lock = threading.Lock()
        self._thread = None
        self._running = False

    def connect(self):
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        for _ in range(60):
            with self._lock:
                if self.session_id:
                    break
            time.sleep(0.3)
        else:
            raise RuntimeError("Timeout: no session_id")
        url = f"{MSG_URL}?session_id={self.session_id}"
        init = {"jsonrpc": "2.0", "id": "init-1", "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "donut-test", "version": "1.0"}}}
        r = requests.post(url, json=init, timeout=30)
        r.raise_for_status()
        deadline = time.time() + 10
        while time.time() < deadline:
            with self._lock:
                if "init-1" not in self._pending:
                    return self.session_id
            time.sleep(0.1)
        return self.session_id

    def _read_loop(self):
        sess = requests.Session()
        sess.headers.update({"Accept": "text/event-stream"})
        try:
            resp = sess.get(SSE_URL, stream=True, timeout=120)
            resp.raise_for_status()
            client = sseclient.SSEClient(resp)
            for event in client.events():
                if not self._running:
                    break
                if event.event == "endpoint":
                    m = re.search(r'session_id=([a-f0-9-]+)', event.data)
                    if m:
                        with self._lock:
                            self.session_id = m.group(1)
                elif event.event == "message":
                    try:
                        parsed = json.loads(event.data)
                    except json.JSONDecodeError:
                        continue
                    rid = parsed.get("id")
                    if rid:
                        with self._lock:
                            if rid in self._pending:
                                self._pending[rid] = parsed
        except Exception as e:
            with self._lock:
                for rid in list(self._pending.keys()):
                    if self._pending[rid] is None:
                        self._pending[rid] = {"error": {"message": str(e)}}

    def call_tool(self, name, args=None, timeout=60):
        if args is None:
            args = {}
        rid = str(uuid.uuid4())
        payload = {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                   "params": {"name": name, "arguments": args}}
        url = f"{MSG_URL}?session_id={self.session_id}"
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        deadline = time.time() + timeout
        with self._lock:
            self._pending[rid] = None
        while time.time() < deadline:
            with self._lock:
                if rid not in self._pending:
                    break
                if self._pending[rid] is not None and "error" in self._pending[rid]:
                    err = self._pending[rid]["error"]
                    raise RuntimeError(f"MCP error: {err}")
            time.sleep(0.1)
        with self._lock:
            resp = self._pending.get(rid)
        if resp is None:
            raise RuntimeError(f"Timeout waiting for tool response: {name}")
        if "error" in resp:
            raise RuntimeError(f"MCP error: {resp['error']}")
        content = resp.get("content", [])
        for c in content:
            if c.get("type") == "text":
                return c["text"]
        return json.dumps(resp)

    def close(self):
        self._running = False


def txt(raw):
    """Extract text from MCP tool response."""
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                content = parsed.get("content", [])
                if content and isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            return c["text"]
                return json.dumps(parsed)
        except json.JSONDecodeError:
            pass
        return raw
    return str(raw)


def main():
    sess = MCPSession()
    try:
        sid = sess.connect()
        print(f"Connected: {sid[:12]}...\n")

        print("1. Connecting to CATIA...")
        r = txt(sess.call_tool("catia_connect", {}))
        print(f"   {r[:120]}\n")

        print("2. Creating new part 'Donut'...")
        r = txt(sess.call_tool("catia_new_part", {"name": "Donut"}))
        print(f"   {r[:120]}\n")

        print("3. Creating sketch on XY plane...")
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
        print(f"   {r[:120]}\n")

        print("4. Drawing circle (cx=50, cy=0, radius=15)...")
        r = txt(sess.call_tool("catia_sketch_circle", {"cx": 50, "cy": 0, "radius": 15}))
        print(f"   {r[:120]}\n")

        print("5. Closing sketch...")
        r = txt(sess.call_tool("catia_close_sketch", {}))
        print(f"   {r[:120]}\n")

        print("6. Creating Shaft (revolve 360° around Z)...")
        r = txt(sess.call_tool("catia_shaft", {
            "sketch_name": "Sketch.1",
            "axis": "z",
            "first_angle": 360,
            "second_angle": 0
        }))
        print(f"   {r[:120]}\n")

        print("7. Listing features...")
        r = txt(sess.call_tool("catia_list_features", {}))
        print(f"   {r[:200]}\n")

        print("✅ Donut created!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        sess.close()


if __name__ == "__main__":
    main()
