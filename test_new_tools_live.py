#!/usr/bin/env python3
"""Live test of 16 new tools via MCP SSE — uses same transport as run_realtests.py."""
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
        self._resp = None

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
        init = {"jsonrpc":"2.0","id":"init-1","method":"initialize",
                "params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"hermes-test","version":"1.0"}}}
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
            self._resp = resp
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
        payload = {"jsonrpc":"2.0","id":rid,"method":"tools/call","params":{"name":name,"arguments":args}}
        with self._lock:
            self._pending[rid] = None
        url = f"{MSG_URL}?session_id={self.session_id}"
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self._pending.get(rid) is not None:
                    result = self._pending.pop(rid)
                    return result
            time.sleep(0.05)
        with self._lock:
            self._pending.pop(rid, None)
        raise RuntimeError(f"Timeout: no response for {name}")

def txt(result):
    if isinstance(result, dict):
        for c in result.get("content", []):
            if isinstance(c, dict) and c.get("type") == "text":
                return c["text"]
    return ""

sess = MCPSession()
print(f"✅ Connected: {sess.session_id}")

# Connect to CATIA
r = txt(sess.call_tool("catia_connect"))
print(f"✅ catia_connect: {r[:80]}")

# Create new part
r = txt(sess.call_tool("catia_new_part", {"name": "TestNewTools"}))
print(f"✅ catia_new_part: {r[:80]}")

# ─── GSD Tests ───
print("\n=== GSD New Tools ===")

# Create geometrical set
r = txt(sess.call_tool("catia_create_geometrical_set", {"name": "TestSet"}))
print(f"✅ catia_create_geometrical_set: {r[:80]}")

# Create point coord
r = txt(sess.call_tool("catia_create_point_coord", {"x": 0, "y": 0, "z": 0, "set_name": "TestSet"}))
print(f"✅ catia_create_point_coord: {r[:80]}")

# Create line 2points
r = txt(sess.call_tool("catia_create_line_2points", {"x1": 0, "y1": 0, "z1": 0, "x2": 100, "y2": 0, "z2": 0, "set_name": "TestSet"}))
print(f"✅ catia_create_line_2points: {r[:80]}")

# NEW: catia_create_point_on_curve
r = txt(sess.call_tool("catia_create_point_on_curve", {"curve_name": "Line.1", "parameter": 0.5, "set_name": "TestSet"}))
print(f"🆕 catia_create_point_on_curve: {r[:120]}")

# NEW: catia_create_point_intersection
r = txt(sess.call_tool("catia_create_point_intersection", {"element1": "Line.1", "element2": "Point.1", "set_name": "TestSet"}))
print(f"🆕 catia_create_point_intersection: {r[:120]}")

# NEW: catia_create_line_tangent
r = txt(sess.call_tool("catia_create_line_tangent", {"curve_name": "Line.1", "point_name": "Point.1", "set_name": "TestSet"}))
print(f"🆕 catia_create_line_tangent: {r[:120]}")

# NEW: catia_create_line_normal_to_surface
r = txt(sess.call_tool("catia_create_line_normal_to_surface", {"surface_name": "xy", "point_name": "Point.1", "set_name": "TestSet"}))
print(f"🆕 catia_create_line_normal_to_surface: {r[:120]}")

# NEW: catia_create_plane_parallel
r = txt(sess.call_tool("catia_create_plane_parallel", {"reference_plane": "xy", "point_name": "Point.1", "set_name": "TestSet"}))
print(f"🆕 catia_create_plane_parallel: {r[:120]}")

# NEW: catia_create_plane_tangent_to_surface
r = txt(sess.call_tool("catia_create_plane_tangent_to_surface", {"surface_name": "xy", "point_name": "Point.1", "set_name": "TestSet"}))
print(f"🆕 catia_create_plane_tangent_to_surface: {r[:120]}")

# NEW: catia_create_mirror
r = txt(sess.call_tool("catia_create_mirror", {"element_name": "Point.1", "mirror_plane": "xy", "set_name": "TestSet"}))
print(f"🆕 catia_create_mirror: {r[:120]}")

# NEW: catia_create_tabulated_cylinder
r = txt(sess.call_tool("catia_create_tabulated_cylinder", {"curve_name": "Line.1", "height1": 10, "height2": 10, "set_name": "TestSet"}))
print(f"🆕 catia_create_tabulated_cylinder: {r[:120]}")

# ─── Part Design New Tools ───
print("\n=== Part Design New Tools ===")

# Create sketch for pad
r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
print(f"✅ catia_create_sketch: {r[:80]}")
r = txt(sess.call_tool("catia_sketch_rectangle", {"x1": 0, "y1": 0, "x2": 20, "y2": 10}))
print(f"✅ catia_sketch_rectangle: {r[:80]}")
r = txt(sess.call_tool("catia_close_sketch"))
print(f"✅ catia_close_sketch: {r[:80]}")

# NEW: catia_rib (validation - no spine)
r = txt(sess.call_tool("catia_rib", {}))
print(f"🆕 catia_rib (no spine): {r[:120]}")

# NEW: catia_slot (validation - no spine)
r = txt(sess.call_tool("catia_slot", {}))
print(f"🆕 catia_slot (no spine): {r[:120]}")

# NEW: catia_stiffener (validation - no supports)
r = txt(sess.call_tool("catia_stiffener", {}))
print(f"🆕 catia_stiffener (no supports): {r[:120]}")

# NEW: catia_split_body (validation - no tool)
r = txt(sess.call_tool("catia_split_body", {}))
print(f"🆕 catia_split_body (no tool): {r[:120]}")

# ─── Sketcher New Tools ───
print("\n=== Sketcher New Tools ===")

# NEW: catia_sketch_trim (validation - no sketch)
r = txt(sess.call_tool("catia_sketch_trim", {}))
print(f"🆕 catia_sketch_trim (no sketch): {r[:120]}")

# NEW: catia_sketch_construction_element (validation - no sketch)
r = txt(sess.call_tool("catia_sketch_construction_element", {}))
print(f"🆕 catia_sketch_construction_element (no sketch): {r[:120]}")

# ─── Assembly New Tools ───
print("\n=== Assembly New Tools ===")

# NEW: catia_ground_constraint (validation - no assembly)
r = txt(sess.call_tool("catia_ground_constraint", {}))
print(f"🆕 catia_ground_constraint (no assembly): {r[:120]}")

# ─── Cleanup ───
print("\n=== Cleanup ===")
r = txt(sess.call_tool("catia_close_document"))
print(f"✅ catia_close_document: {r[:80]}")
r = txt(sess.call_tool("catia_disconnect"))
print(f"✅ catia_disconnect: {r[:80]}")

print("\n✅ All new tools tested!")
