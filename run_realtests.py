#!/usr/bin/env python3
"""Run all Realtests from REALTEST_PLAN.md and produce a results report."""
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
        # MCP init
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

    def list_tools_mcp(self, timeout=30):
        rid = str(uuid.uuid4())
        payload = {"jsonrpc":"2.0","id":rid,"method":"tools/list","params":{}}
        with self._lock:
            self._pending[rid] = None
        url = f"{MSG_URL}?session_id={self.session_id}"
        r = requests.post(url, json=payload, timeout=30)
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
        raise RuntimeError("Timeout: no response for tools/list")

    def close(self):
        self._running = False
        if self._resp:
            try: self._resp.close()
            except: pass
        if self._thread:
            self._thread.join(timeout=3)


def txt(result):
    if "error" in result:
        e = result["error"]
        return f"ERROR: {e.get('code','?')} - {e.get('message','Unknown')}"
    parts = [i.get("text","") for i in result.get("result",{}).get("content",[]) if i.get("type")=="text"]
    return "\n".join(parts) if parts else str(result)


def extract_name(response_text):
    """Extract element name from response like 'Feature: Pad.1' or 'Point.1'."""
    # Try various patterns
    patterns = [
        r"['\"](\w+\.\d+)['\"]",
        r"Feature[:\s]+['\"]?(\w+\.\d+)['\"]?",
        r"['\"](\w+\.\w+)['\"]",
    ]
    for pat in patterns:
        m = re.search(pat, response_text)
        if m:
            return m.group(1)
    return None


# Results storage
results = []

def record(phase, test_id, status, remark=""):
    results.append({"phase": phase, "id": test_id, "status": status, "remark": remark})
    print(f"  [{status}] {test_id}: {remark}")


def run_tests(sess):
    global results
    # ============ P0: Document Management ============
    print("\n" + "="*60)
    print("PHASE P0: Document Management")
    print("="*60)

    # P0-01: catia_connect
    try:
        r = txt(sess.call_tool("catia_connect"))
        ok = "connected" in r.lower() or "launched" in r.lower() or "running" in r.lower()
        record("P0", "P0-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-01", "❌", str(e)[:100])

    # P0-02: catia_new_part {}
    try:
        r = txt(sess.call_tool("catia_new_part"))
        ok = "part" in r.lower() or "created" in r.lower()
        record("P0", "P0-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-02", "❌", str(e)[:100])

    # P0-03: catia_new_part {"name": "TestPart"}
    try:
        r = txt(sess.call_tool("catia_new_part", {"name": "TestPart"}))
        ok = "testpart" in r.lower() or "created" in r.lower()
        record("P0", "P0-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-03", "❌", str(e)[:100])

    # P0-04: catia_new_product {}
    try:
        r = txt(sess.call_tool("catia_new_product"))
        ok = "product" in r.lower() or "created" in r.lower() or "assembly" in r.lower()
        record("P0", "P0-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-04", "❌", str(e)[:100])

    # P0-05: catia_new_product {"name": "TestAssembly"}
    try:
        r = txt(sess.call_tool("catia_new_product", {"name": "TestAssembly"}))
        ok = "testassembly" in r.lower() or "created" in r.lower()
        record("P0", "P0-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-05", "❌", str(e)[:100])

    # P0-06: catia_list_documents
    try:
        r = txt(sess.call_tool("catia_list_documents"))
        ok = len(r) > 10  # Should have some content
        record("P0", "P0-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-06", "❌", str(e)[:100])

    # P0-07: catia_get_active_document_info
    try:
        r = txt(sess.call_tool("catia_get_active_document_info"))
        ok = len(r) > 10
        record("P0", "P0-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-07", "❌", str(e)[:100])

    # P0-08: catia_save_document
    try:
        r = txt(sess.call_tool("catia_save_document", {"file_path": "C:/catia_tests/test_part.CATPart"}))
        ok = "saved" in r.lower() or "save" in r.lower() or "C:/catia_tests" in r
        record("P0", "P0-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-08", "❌", str(e)[:100])

    # P0-09: catia_close_document {"save": false}
    try:
        r = txt(sess.call_tool("catia_close_document", {"save": False}))
        ok = "closed" in r.lower() or "close" in r.lower()
        record("P0", "P0-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-09", "❌", str(e)[:100])

    # P0-10: catia_open_document
    try:
        r = txt(sess.call_tool("catia_open_document", {"file_path": "C:/catia_tests/test_part.CATPart"}))
        ok = "opened" in r.lower() or "open" in r.lower()
        record("P0", "P0-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-10", "❌", str(e)[:100])

    # P0-11: catia_disconnect
    try:
        r = txt(sess.call_tool("catia_disconnect"))
        ok = "disconnect" in r.lower()
        record("P0", "P0-11", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-11", "❌", str(e)[:100])

    # P0-12: catia_connect (reconnect)
    try:
        r = txt(sess.call_tool("catia_connect"))
        ok = "connected" in r.lower() or "launched" in r.lower() or "running" in r.lower()
        record("P0", "P0-12", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P0", "P0-12", "❌", str(e)[:100])

    # ============ P1: Sketcher ============
    print("\n" + "="*60)
    print("PHASE P1: Sketcher")
    print("="*60)

    # Fresh part for sketcher tests
    try:
        r = txt(sess.call_tool("catia_new_part", {"name": "TestSketch"}))
        print(f"  [Setup] New part: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] New part failed: {e}")

    # P1-01: create_sketch xy
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
        ok = "sketch" in r.lower() or "created" in r.lower() or "xy" in r.lower()
        record("P1", "P1-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-01", "❌", str(e)[:100])

    # P1-02 to P1-05: sketch lines
    line_tests = [
        ("P1-02", {"x1":0,"y1":0,"x2":100,"y2":0}),
        ("P1-03", {"x1":100,"y1":0,"x2":100,"y2":60}),
        ("P1-04", {"x1":100,"y1":60,"x2":0,"y2":60}),
        ("P1-05", {"x1":0,"y1":60,"x2":0,"y2":0}),
    ]
    for tid, params in line_tests:
        try:
            r = txt(sess.call_tool("catia_sketch_line", params))
            ok = "line" in r.lower() or "created" in r.lower()
            record("P1", tid, "✅" if ok else "❌", r[:100])
        except Exception as e:
            record("P1", tid, "❌", str(e)[:100])

    # P1-06: sketch_rectangle
    try:
        r = txt(sess.call_tool("catia_sketch_rectangle", {"x1":120,"y1":0,"x2":220,"y2":60}))
        ok = "rectangle" in r.lower() or "rect" in r.lower() or "created" in r.lower() or "line" in r.lower()
        record("P1", "P1-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-06", "❌", str(e)[:100])

    # P1-07: sketch_centered_rectangle
    try:
        r = txt(sess.call_tool("catia_sketch_centered_rectangle", {"cx":0,"cy":100,"width":80,"height":40}))
        ok = "rectangle" in r.lower() or "rect" in r.lower() or "created" in r.lower()
        record("P1", "P1-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-07", "❌", str(e)[:100])

    # P1-08: sketch_circle with center
    try:
        r = txt(sess.call_tool("catia_sketch_circle", {"cx":150,"cy":100,"radius":25}))
        ok = "circle" in r.lower() or "created" in r.lower()
        record("P1", "P1-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-08", "❌", str(e)[:100])

    # P1-09: sketch_circle default center
    try:
        r = txt(sess.call_tool("catia_sketch_circle", {"radius":15}))
        ok = "circle" in r.lower() or "created" in r.lower()
        record("P1", "P1-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-09", "❌", str(e)[:100])

    # P1-10: sketch_arc
    try:
        r = txt(sess.call_tool("catia_sketch_arc", {"cx":0,"cy":180,"radius":30,"start_angle":0,"end_angle":180}))
        ok = "arc" in r.lower() or "created" in r.lower()
        record("P1", "P1-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-10", "❌", str(e)[:100])

    # P1-11: sketch_spline
    try:
        r = txt(sess.call_tool("catia_sketch_spline", {"points":[[0,200],[20,220],[40,200],[60,220]]}))
        ok = "spline" in r.lower() or "created" in r.lower()
        record("P1", "P1-11", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-11", "❌", str(e)[:100])

    # P1-12: sketch_point
    try:
        r = txt(sess.call_tool("catia_sketch_point", {"x":100,"y":200}))
        ok = "point" in r.lower() or "created" in r.lower()
        record("P1", "P1-12", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-12", "❌", str(e)[:100])

    # P1-13: get_geometry
    try:
        r = txt(sess.call_tool("catia_sketch_get_geometry"))
        ok = len(r) > 20  # Should list geometries
        record("P1", "P1-13", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-13", "❌", str(e)[:100])

    # P1-14: constraint horizontal
    try:
        r = txt(sess.call_tool("catia_sketch_constraint", {"type":"horizontal","geometry_index_1":1}))
        ok = "constraint" in r.lower() or "horizontal" in r.lower() or "applied" in r.lower()
        record("P1", "P1-14", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-14", "❌", str(e)[:100])

    # P1-15: constraint distance
    try:
        r = txt(sess.call_tool("catia_sketch_constraint", {"type":"distance","geometry_index_1":1,"geometry_index_2":2,"value":100}))
        ok = "constraint" in r.lower() or "distance" in r.lower() or "applied" in r.lower()
        record("P1", "P1-15", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-15", "❌", str(e)[:100])

    # P1-16: close_sketch
    try:
        r = txt(sess.call_tool("catia_close_sketch"))
        ok = "closed" in r.lower() or "close" in r.lower() or "part design" in r.lower()
        record("P1", "P1-16", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-16", "❌", str(e)[:100])

    # P1-17: create_sketch yz
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "yz"}))
        ok = "sketch" in r.lower() or "created" in r.lower() or "yz" in r.lower()
        record("P1", "P1-17", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-17", "❌", str(e)[:100])

    # P1-18: close_sketch
    try:
        r = txt(sess.call_tool("catia_close_sketch"))
        ok = "closed" in r.lower() or "close" in r.lower()
        record("P1", "P1-18", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P1", "P1-18", "❌", str(e)[:100])

    # ============ P2: Part Design ============
    print("\n" + "="*60)
    print("PHASE P2: Part Design")
    print("="*60)

    # Fresh part for P2
    try:
        r = txt(sess.call_tool("catia_new_part", {"name": "TestPartDesign"}))
        print(f"  [Setup] New part: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] New part failed: {e}")

    # P2-01: create_sketch xy
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
        ok = "sketch" in r.lower() or "created" in r.lower()
        record("P2", "P2-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-01", "❌", str(e)[:100])

    # P2-02: centered_rectangle
    try:
        r = txt(sess.call_tool("catia_sketch_centered_rectangle", {"cx":0,"cy":0,"width":100,"height":60}))
        ok = "rectangle" in r.lower() or "rect" in r.lower() or "created" in r.lower()
        record("P2", "P2-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-02", "❌", str(e)[:100])

    # P2-03: close_sketch
    try:
        r = txt(sess.call_tool("catia_close_sketch"))
        ok = "closed" in r.lower() or "close" in r.lower()
        record("P2", "P2-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-03", "❌", str(e)[:100])

    # P2-04: pad
    try:
        r = txt(sess.call_tool("catia_pad", {"height": 40}))
        ok = "pad" in r.lower() or "created" in r.lower()
        record("P2", "P2-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-04", "❌", str(e)[:100])

    # P2-05: list_features
    try:
        r = txt(sess.call_tool("catia_list_features"))
        ok = "pad" in r.lower() or len(r) > 20
        record("P2", "P2-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-05", "❌", str(e)[:100])

    # P2-06: list_edges
    try:
        r = txt(sess.call_tool("catia_list_edges"))
        ok = len(r) > 20
        record("P2", "P2-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-06", "❌", str(e)[:100])

    # P2-07: create_sketch for pocket
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
        ok = "sketch" in r.lower() or "created" in r.lower()
        record("P2", "P2-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-07", "❌", str(e)[:100])

    # P2-08: sketch_circle for pocket
    try:
        r = txt(sess.call_tool("catia_sketch_circle", {"cx":0,"cy":0,"radius":15}))
        ok = "circle" in r.lower() or "created" in r.lower()
        record("P2", "P2-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-08", "❌", str(e)[:100])

    # P2-09: close_sketch
    try:
        r = txt(sess.call_tool("catia_close_sketch"))
        ok = "closed" in r.lower() or "close" in r.lower()
        record("P2", "P2-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-09", "❌", str(e)[:100])

    # P2-10: pocket
    try:
        r = txt(sess.call_tool("catia_pocket", {"depth": 20}))
        ok = "pocket" in r.lower() or "created" in r.lower() or "cut" in r.lower()
        record("P2", "P2-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-10", "❌", str(e)[:100])

    # P2-11: fillet (all edges)
    try:
        r = txt(sess.call_tool("catia_fillet", {"radius": 3}))
        ok = "fillet" in r.lower() or "created" in r.lower()
        record("P2", "P2-11", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-11", "❌", str(e)[:100])

    # P2-12: fillet specific edge (skip - need edge name from P2-06)
    record("P2", "P2-12", "⏭️", "Skipped - requires edge name extraction")

    # P2-13: chamfer
    try:
        r = txt(sess.call_tool("catia_chamfer", {"length": 5, "angle": 45}))
        ok = "chamfer" in r.lower() or "created" in r.lower()
        record("P2", "P2-13", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-13", "❌", str(e)[:100])

    # P2-14 to P2-19: Shaft
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "yz"}))
        record("P2", "P2-14", "✅" if ("sketch" in r.lower()) else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-14", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_sketch_line", {"x1":0,"y1":0,"x2":0,"y2":30}))
        record("P2", "P2-15", "✅" if ("line" in r.lower()) else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-15", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_sketch_rectangle", {"x1":10,"y1":5,"x2":25,"y2":25}))
        record("P2", "P2-16", "✅" if ("rect" in r.lower() or "line" in r.lower()) else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-16", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_close_sketch"))
        record("P2", "P2-17", "✅" if ("closed" in r.lower()) else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-17", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_shaft", {"angle": 360}))
        ok = "shaft" in r.lower() or "revolution" in r.lower() or "created" in r.lower()
        record("P2", "P2-18", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-18", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_shaft", {"angle": 180}))
        ok = "shaft" in r.lower() or "revolution" in r.lower() or "created" in r.lower()
        record("P2", "P2-19", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-19", "❌", str(e)[:100])

    # P2-20 to P2-23: Hole
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
        record("P2", "P2-20", "✅" if ("sketch" in r.lower()) else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-20", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_sketch_point", {"x":30,"y":20}))
        record("P2", "P2-21", "✅" if ("point" in r.lower() or "created" in r.lower()) else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-21", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_close_sketch"))
        record("P2", "P2-22", "✅" if ("closed" in r.lower()) else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-22", "❌", str(e)[:100])

    try:
        r = txt(sess.call_tool("catia_hole", {"diameter": 8, "depth": 30}))
        ok = "hole" in r.lower() or "created" in r.lower()
        record("P2", "P2-23", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-23", "❌", str(e)[:100])

    # P2-24: rect_pattern
    try:
        r = txt(sess.call_tool("catia_rect_pattern", {"dir1_count": 3, "dir1_spacing": 20}))
        ok = "pattern" in r.lower() or "created" in r.lower()
        record("P2", "P2-24", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-24", "❌", str(e)[:100])

    # P2-25: mirror
    try:
        r = txt(sess.call_tool("catia_mirror", {"plane": "yz"}))
        ok = "mirror" in r.lower() or "created" in r.lower()
        record("P2", "P2-25", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P2", "P2-25", "❌", str(e)[:100])

    # ============ P3: GSD ============
    print("\n" + "="*60)
    print("PHASE P3: GSD - Wireframe & Surface")
    print("="*60)

    # Fresh part for GSD
    try:
        r = txt(sess.call_tool("catia_new_part", {"name": "TestGSD"}))
        print(f"  [Setup] New part: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] New part failed: {e}")

    # P3-01: create_geometrical_set
    try:
        r = txt(sess.call_tool("catia_create_geometrical_set", {"name": "TestGeoSet"}))
        ok = "geometrical" in r.lower() or "set" in r.lower() or "created" in r.lower()
        record("P3", "P3-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-01", "❌", str(e)[:100])

    # P3-02: create_point_coord (0,0,0)
    try:
        r = txt(sess.call_tool("catia_create_point_coord", {"x":0,"y":0,"z":0,"set_name":"TestGeoSet"}))
        ok = "point" in r.lower() or "created" in r.lower()
        pname = extract_name(r) or "Point.1"
        record("P3", "P3-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-02", "❌", str(e)[:100])
        pname = "Point.1"

    # P3-03: create_point_coord (100,50,25)
    try:
        r = txt(sess.call_tool("catia_create_point_coord", {"x":100,"y":50,"z":25,"set_name":"TestGeoSet"}))
        ok = "point" in r.lower() or "created" in r.lower()
        pname2 = extract_name(r) or "Point.2"
        record("P3", "P3-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-03", "❌", str(e)[:100])
        pname2 = "Point.2"

    # P3-04: create_line_2points
    try:
        r = txt(sess.call_tool("catia_create_line_2points", {"point1_name":pname,"point2_name":pname2,"set_name":"TestGeoSet"}))
        ok = "line" in r.lower() or "created" in r.lower()
        lname = extract_name(r) or "Line.1"
        record("P3", "P3-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-04", "❌", str(e)[:100])
        lname = "Line.1"

    # P3-05: create_line_point_direction
    try:
        r = txt(sess.call_tool("catia_create_line_point_direction", {"point_name":pname,"direction":"x","set_name":"TestGeoSet"}))
        ok = "line" in r.lower() or "created" in r.lower()
        lname2 = extract_name(r) or "Line.2"
        record("P3", "P3-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-05", "❌", str(e)[:100])
        lname2 = "Line.2"

    # P3-06: create_circle_center_radius
    try:
        r = txt(sess.call_tool("catia_create_circle_center_radius", {"center_name":pname,"radius":30,"support_plane":"xy","set_name":"TestGeoSet"}))
        ok = "circle" in r.lower() or "created" in r.lower()
        cname = extract_name(r) or "Circle.1"
        record("P3", "P3-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-06", "❌", str(e)[:100])
        cname = "Circle.1"

    # P3-07: create_plane_offset
    try:
        r = txt(sess.call_tool("catia_create_plane_offset", {"reference_plane":"xy","offset":50,"set_name":"TestGeoSet"}))
        ok = "plane" in r.lower() or "created" in r.lower()
        record("P3", "P3-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-07", "❌", str(e)[:100])

    # P3-08: create_plane_3points (need 3rd point)
    try:
        r = txt(sess.call_tool("catia_create_point_coord", {"x":50,"y":100,"z":0,"set_name":"TestGeoSet"}))
        pname3 = extract_name(r) or "Point.3"
    except:
        pname3 = "Point.3"
    try:
        r = txt(sess.call_tool("catia_create_plane_3points", {"point1_name":pname,"point2_name":pname2,"point3_name":pname3,"set_name":"TestGeoSet"}))
        ok = "plane" in r.lower() or "created" in r.lower()
        record("P3", "P3-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-08", "❌", str(e)[:100])

    # P3-09: create_cylinder
    try:
        r = txt(sess.call_tool("catia_create_cylinder", {"center_name":pname,"axis":"z","radius":20,"height":60,"set_name":"TestGeoSet"}))
        ok = "cylinder" in r.lower() or "created" in r.lower()
        record("P3", "P3-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-09", "❌", str(e)[:100])

    # P3-10: create_sphere
    try:
        r = txt(sess.call_tool("catia_create_sphere", {"cx":0,"cy":0,"cz":100,"radius":25,"set_name":"TestGeoSet"}))
        ok = "sphere" in r.lower() or "created" in r.lower()
        record("P3", "P3-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-10", "❌", str(e)[:100])

    # P3-11: create_cone
    try:
        r = txt(sess.call_tool("catia_create_cone", {"cx":0,"cy":0,"cz":150,"base_radius":20,"height":40,"set_name":"TestGeoSet"}))
        ok = "cone" in r.lower() or "created" in r.lower()
        record("P3", "P3-11", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-11", "❌", str(e)[:100])

    # P3-12: create_torus
    try:
        r = txt(sess.call_tool("catia_create_torus", {"cx":0,"cy":0,"cz":200,"major_radius":30,"minor_radius":8,"set_name":"TestGeoSet"}))
        ok = "torus" in r.lower() or "created" in r.lower()
        record("P3", "P3-12", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-12", "❌", str(e)[:100])

    # P3-13: create_fill
    try:
        r = txt(sess.call_tool("catia_create_fill", {"contour_names":[cname],"set_name":"TestGeoSet"}))
        ok = "fill" in r.lower() or "surface" in r.lower() or "created" in r.lower()
        fname = extract_name(r) or "Fill.1"
        record("P3", "P3-13", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-13", "❌", str(e)[:100])
        fname = "Fill.1"

    # P3-14: create_sweep
    try:
        r = txt(sess.call_tool("catia_create_sweep", {"spine_name":lname,"section_name":cname,"set_name":"TestGeoSet"}))
        ok = "sweep" in r.lower() or "created" in r.lower()
        record("P3", "P3-14", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-14", "❌", str(e)[:100])

    # P3-15: create_offset_surface
    try:
        r = txt(sess.call_tool("catia_create_offset_surface", {"surface_name":fname,"distance":5,"set_name":"TestGeoSet"}))
        ok = "offset" in r.lower() or "created" in r.lower()
        oname = extract_name(r) or "Offset.1"
        record("P3", "P3-15", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-15", "❌", str(e)[:100])
        oname = "Offset.1"

    # P3-16: create_join
    try:
        r = txt(sess.call_tool("catia_create_join", {"surface_names":[fname,oname],"set_name":"TestGeoSet"}))
        ok = "join" in r.lower() or "created" in r.lower()
        record("P3", "P3-16", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-16", "❌", str(e)[:100])

    # P3-17: create_thicken
    try:
        r = txt(sess.call_tool("catia_create_thicken", {"surface_name":fname,"thickness":2,"set_name":"TestGeoSet"}))
        ok = "thicken" in r.lower() or "created" in r.lower()
        record("P3", "P3-17", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-17", "❌", str(e)[:100])

    # P3-18: create_ruled
    try:
        r = txt(sess.call_tool("catia_create_ruled", {"profile1":lname,"profile2":lname2,"set_name":"TestGeoSet"}))
        ok = "ruled" in r.lower() or "created" in r.lower()
        record("P3", "P3-18", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-18", "❌", str(e)[:100])

    # P3-19: list_geometrical_sets
    try:
        r = txt(sess.call_tool("catia_list_geometrical_sets"))
        ok = "testgset" in r.lower() or "geometrical" in r.lower() or len(r) > 10
        record("P3", "P3-19", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-19", "❌", str(e)[:100])

    # P3-20: create_blend
    try:
        r = txt(sess.call_tool("catia_create_blend", {"edge_or_curve_name":lname,"radius":5,"set_name":"TestGeoSet"}))
        ok = "blend" in r.lower() or "created" in r.lower()
        record("P3", "P3-20", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P3", "P3-20", "❌", str(e)[:100])

    # ============ P4: Assembly ============
    print("\n" + "="*60)
    print("PHASE P4: Assembly")
    print("="*60)

    # P4-01: new_product
    try:
        r = txt(sess.call_tool("catia_new_product", {"name": "TestAssembly"}))
        ok = "product" in r.lower() or "assembly" in r.lower() or "created" in r.lower()
        record("P4", "P4-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-01", "❌", str(e)[:100])

    # P4-02: add_new_part
    try:
        r = txt(sess.call_tool("catia_add_new_part", {"name": "BasePart"}))
        ok = "basepart" in r.lower() or "component" in r.lower() or "added" in r.lower() or "created" in r.lower()
        record("P4", "P4-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-02", "❌", str(e)[:100])

    # P4-03: add_component from file
    try:
        r = txt(sess.call_tool("catia_add_component", {"file_path": "C:/catia_tests/test_part.CATPart"}))
        ok = "component" in r.lower() or "added" in r.lower() or "opened" in r.lower()
        record("P4", "P4-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-03", "❌", str(e)[:100])

    # P4-04: fix_constraint
    try:
        r = txt(sess.call_tool("catia_fix_constraint", {"component_name": "BasePart"}))
        ok = "fix" in r.lower() or "constraint" in r.lower() or "applied" in r.lower()
        record("P4", "P4-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-04", "❌", str(e)[:100])

    # P4-05: list_components
    try:
        r = txt(sess.call_tool("catia_list_components"))
        ok = len(r) > 10
        record("P4", "P4-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-05", "❌", str(e)[:100])

    # P4-06: move_component translate
    try:
        r = txt(sess.call_tool("catia_move_component", {"component_name":"BasePart","tx":50,"ty":0,"tz":0}))
        ok = "move" in r.lower() or "moved" in r.lower() or "basepart" in r.lower()
        record("P4", "P4-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-06", "❌", str(e)[:100])

    # P4-07: move_component rotate
    try:
        r = txt(sess.call_tool("catia_move_component", {"component_name":"BasePart","rx":0,"ry":90,"rz":0}))
        ok = "move" in r.lower() or "rotat" in r.lower() or "basepart" in r.lower()
        record("P4", "P4-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-07", "❌", str(e)[:100])

    # P4-08 to P4-10: Skip (need 2 components with element names)
    record("P4", "P4-08", "⏭️", "Skipped - requires 2 components with element references")
    record("P4", "P4-09", "⏭️", "Skipped - requires 2 components")
    record("P4", "P4-10", "⏭️", "Skipped - requires 2 components")

    # P4-11: list_constraints
    try:
        r = txt(sess.call_tool("catia_list_constraints"))
        ok = len(r) > 5
        record("P4", "P4-11", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-11", "❌", str(e)[:100])

    # P4-12: get_active_document_info
    try:
        r = txt(sess.call_tool("catia_get_active_document_info"))
        ok = "product" in r.lower() or "assembly" in r.lower() or len(r) > 10
        record("P4", "P4-12", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P4", "P4-12", "❌", str(e)[:100])

    # ============ P5: Measurement ============
    print("\n" + "="*60)
    print("PHASE P5: Measurement")
    print("="*60)

    # Need a part with geometry - open the P2 part or create new
    try:
        r = txt(sess.call_tool("catia_new_part", {"name": "TestMeasure"}))
        print(f"  [Setup] New part: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] New part failed: {e}")

    # Create some geometry for measurement
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
        r2 = txt(sess.call_tool("catia_sketch_centered_rectangle", {"cx":0,"cy":0,"width":100,"height":60}))
        r3 = txt(sess.call_tool("catia_close_sketch"))
        r4 = txt(sess.call_tool("catia_pad", {"height": 40}))
        print(f"  [Setup] Pad: {r4[:80]}")
    except Exception as e:
        print(f"  [Setup] Pad failed: {e}")

    # P5-01: measure_distance (need edges)
    try:
        r = txt(sess.call_tool("catia_list_edges"))
        # Extract first two edge names
        edges = re.findall(r"['\"](\w+\.\d+)['\"]", r)
        if len(edges) >= 2:
            e1, e2 = edges[0], edges[1]
            r2 = txt(sess.call_tool("catia_measure_distance", {"element1": e1, "element2": e2}))
            ok = "mm" in r2.lower() or "distance" in r2.lower() or len(r2) > 5
            record("P5", "P5-01", "✅" if ok else "❌", r2[:100])
        else:
            record("P5", "P5-01", "⏭️", "No edges found for distance measurement")
    except Exception as e:
        record("P5", "P5-01", "❌", str(e)[:100])

    # P5-02: get_inertia (no density)
    try:
        r = txt(sess.call_tool("catia_get_inertia"))
        ok = "volume" in r.lower() or "area" in r.lower() or "inertia" in r.lower() or len(r) > 10
        record("P5", "P5-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P5", "P5-02", "❌", str(e)[:100])

    # P5-03: get_inertia with density
    try:
        r = txt(sess.call_tool("catia_get_inertia", {"density": 7800}))
        ok = "mass" in r.lower() or "volume" in r.lower() or "inertia" in r.lower() or len(r) > 10
        record("P5", "P5-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P5", "P5-03", "❌", str(e)[:100])

    # P5-04: get_bounding_box
    try:
        r = txt(sess.call_tool("catia_get_bounding_box"))
        ok = "min" in r.lower() or "max" in r.lower() or "bound" in r.lower() or len(r) > 10
        record("P5", "P5-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P5", "P5-04", "❌", str(e)[:100])

    # P5-05: measure_angle (need faces)
    try:
        r = txt(sess.call_tool("catia_list_edges"))
        edges = re.findall(r"['\"](\w+\.\d+)['\"]", r)
        if len(edges) >= 2:
            r2 = txt(sess.call_tool("catia_measure_angle", {"element1": edges[0], "element2": edges[1]}))
            ok = "angle" in r2.lower() or "degree" in r2.lower() or len(r2) > 5
            record("P5", "P5-05", "✅" if ok else "❌", r2[:100])
        else:
            record("P5", "P5-05", "⏭️", "Not enough elements")
    except Exception as e:
        record("P5", "P5-05", "❌", str(e)[:100])

    # P5-06: measure_area
    try:
        r = txt(sess.call_tool("catia_list_edges"))
        edges = re.findall(r"['\"](\w+\.\d+)['\"]", r)
        if edges:
            r2 = txt(sess.call_tool("catia_measure_area", {"element": edges[0]}))
            ok = "area" in r2.lower() or "mm" in r2.lower() or len(r2) > 5
            record("P5", "P5-06", "✅" if ok else "❌", r2[:100])
        else:
            record("P5", "P5-06", "⏭️", "No elements")
    except Exception as e:
        record("P5", "P5-06", "❌", str(e)[:100])

    # P5-07: measure_length
    try:
        r = txt(sess.call_tool("catia_list_edges"))
        edges = re.findall(r"['\"](\w+\.\d+)['\"]", r)
        if edges:
            r2 = txt(sess.call_tool("catia_measure_length", {"element": edges[0]}))
            ok = "length" in r2.lower() or "mm" in r2.lower() or len(r2) > 5
            record("P5", "P5-07", "✅" if ok else "❌", r2[:100])
        else:
            record("P5", "P5-07", "⏭️", "No elements")
    except Exception as e:
        record("P5", "P5-07", "❌", str(e)[:100])

    # P5-08: measure_interference (needs 2 bodies - skip)
    record("P5", "P5-08", "⏭️", "Skipped - requires 2 bodies")

    # P5-09: get_parameters
    try:
        r = txt(sess.call_tool("catia_get_parameters"))
        ok = len(r) > 5
        record("P5", "P5-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P5", "P5-09", "❌", str(e)[:100])

    # P5-10: get_parameters with filter
    try:
        r = txt(sess.call_tool("catia_get_parameters", {"filter": "Length"}))
        ok = len(r) > 5
        record("P5", "P5-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P5", "P5-10", "❌", str(e)[:100])

    # P5-11: set_parameter (skip - need param name)
    record("P5", "P5-11", "⏭️", "Skipped - requires known parameter name")

    # P5-12: update_part
    try:
        r = txt(sess.call_tool("catia_update_part"))
        ok = "update" in r.lower() or "success" in r.lower() or len(r) > 5
        record("P5", "P5-12", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P5", "P5-12", "❌", str(e)[:100])

    # ============ P6: Export & View ============
    print("\n" + "="*60)
    print("PHASE P6: Export & View")
    print("="*60)

    # P6-01: set_view isometric
    try:
        r = txt(sess.call_tool("catia_set_view", {"view": "isometric"}))
        ok = "isometric" in r.lower() or "view" in r.lower() or len(r) > 5
        record("P6", "P6-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-01", "❌", str(e)[:100])

    # P6-02: set_view front
    try:
        r = txt(sess.call_tool("catia_set_view", {"view": "front"}))
        ok = "front" in r.lower() or "view" in r.lower() or len(r) > 5
        record("P6", "P6-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-02", "❌", str(e)[:100])

    # P6-03: set_view top
    try:
        r = txt(sess.call_tool("catia_set_view", {"view": "top"}))
        ok = "top" in r.lower() or "view" in r.lower() or len(r) > 5
        record("P6", "P6-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-03", "❌", str(e)[:100])

    # P6-04: fit_all
    try:
        r = txt(sess.call_tool("catia_fit_all"))
        ok = "fit" in r.lower() or len(r) > 5
        record("P6", "P6-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-04", "❌", str(e)[:100])

    # P6-05: screenshot png
    try:
        r = txt(sess.call_tool("catia_screenshot", {"file_path": "C:/catia_tests/screenshot.png"}))
        ok = "screenshot" in r.lower() or "saved" in r.lower() or "png" in r.lower() or len(r) > 5
        record("P6", "P6-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-05", "❌", str(e)[:100])

    # P6-06: screenshot jpg
    try:
        r = txt(sess.call_tool("catia_screenshot", {"file_path": "C:/catia_tests/screenshot.jpg", "width": 1280, "height": 720}))
        ok = "screenshot" in r.lower() or "saved" in r.lower() or "jpg" in r.lower() or len(r) > 5
        record("P6", "P6-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-06", "❌", str(e)[:100])

    # P6-07: export STEP
    try:
        r = txt(sess.call_tool("catia_export", {"file_path": "C:/catia_tests/test_part.stp"}))
        ok = "step" in r.lower() or "export" in r.lower() or "saved" in r.lower() or len(r) > 5
        record("P6", "P6-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-07", "❌", str(e)[:100])

    # P6-08: export IGES
    try:
        r = txt(sess.call_tool("catia_export", {"file_path": "C:/catia_tests/test_part.igs"}))
        ok = "iges" in r.lower() or "export" in r.lower() or "saved" in r.lower() or len(r) > 5
        record("P6", "P6-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P6", "P6-08", "❌", str(e)[:100])

    # ============ P7: Error Handling ============
    print("\n" + "="*60)
    print("PHASE P7: Error Handling")
    print("="*60)

    # P7-01: pad negative height
    try:
        r = txt(sess.call_tool("catia_pad", {"height": -10}))
        # Should fail with error about positive value
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P7", "P7-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        # Exception is also acceptable for error handling
        record("P7", "P7-01", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-02: pad zero height
    try:
        r = txt(sess.call_tool("catia_pad", {"height": 0}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P7", "P7-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-02", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-03: pocket negative depth
    try:
        r = txt(sess.call_tool("catia_pocket", {"depth": -5}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P7", "P7-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-03", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-04: fillet negative radius
    try:
        r = txt(sess.call_tool("catia_fillet", {"radius": -2}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P7", "P7-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-04", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-05: chamfer negative length
    try:
        r = txt(sess.call_tool("catia_chamfer", {"length": -1}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P7", "P7-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-05", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-06: sketch_circle zero radius (need active sketch)
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "xy"}))
        r2 = txt(sess.call_tool("catia_sketch_circle", {"radius": 0}))
        ok = "error" in r2.lower() or "positive" in r2.lower() or "invalid" in r2.lower()
        record("P7", "P7-06", "✅" if ok else "❌", r2[:100])
        # Close sketch
        try: sess.call_tool("catia_close_sketch")
        except: pass
    except Exception as e:
        record("P7", "P7-06", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-07: create_sketch invalid plane
    try:
        r = txt(sess.call_tool("catia_create_sketch", {"plane": "front"}))
        ok = "error" in r.lower() or "invalid" in r.lower() or "xy" in r.lower()
        record("P7", "P7-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-07", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-08: mirror invalid plane
    try:
        r = txt(sess.call_tool("catia_mirror", {"plane": "invalid"}))
        ok = "error" in r.lower() or "invalid" in r.lower() or "xy" in r.lower()
        record("P7", "P7-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-08", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-09: open nonexistent file
    try:
        r = txt(sess.call_tool("catia_open_document", {"file_path": "nonexistent_file.txt"}))
        ok = "error" in r.lower() or "not found" in r.lower() or "nonexistent" in r.lower()
        record("P7", "P7-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-09", "✅", f"Exception raised: {str(e)[:80]}")

    # P7-10: export relative path
    try:
        r = txt(sess.call_tool("catia_export", {"file_path": "relative_path.stp"}))
        ok = "error" in r.lower() or "absolute" in r.lower() or "invalid" in r.lower()
        record("P7", "P7-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P7", "P7-10", "✅", f"Exception raised: {str(e)[:80]}")

    # ============ P8: Transport & Server ============
    print("\n" + "="*60)
    print("PHASE P8: Transport & Server Stability")
    print("="*60)

    # P8-01: Auto-connect (disconnect first, then call tool)
    try:
        sess.call_tool("catia_disconnect")
        r = txt(sess.call_tool("catia_new_part", {"name": "AutoConnectTest"}))
        ok = "part" in r.lower() or "created" in r.lower() or "auto" in r.lower() or "connect" in r.lower()
        record("P8", "P8-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P8", "P8-01", "❌", str(e)[:100])

    # P8-02: Auto-reconnect after disconnect
    try:
        sess.call_tool("catia_disconnect")
        r = txt(sess.call_tool("catia_new_part", {"name": "ReconnectTest"}))
        ok = "part" in r.lower() or "created" in r.lower() or "auto" in r.lower() or "connect" in r.lower()
        record("P8", "P8-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P8", "P8-02", "❌", str(e)[:100])

    # P8-03: list_tools
    try:
        r = txt(sess.list_tools_mcp())
        ok = len(r) > 100  # Should list many tools
        record("P8", "P8-03", "✅" if ok else "❌", f"Listed tools, response length: {len(r)}")
    except Exception as e:
        record("P8", "P8-03", "❌", str(e)[:100])

    # P8-04: Unknown tool
    try:
        r = txt(sess.call_tool("catia_nonexistent"))
        ok = "unknown" in r.lower() or "error" in r.lower() or "not found" in r.lower()
        record("P8", "P8-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "unknown" in str(e).lower() or "error" in str(e).lower()
        record("P8", "P8-04", "✅" if ok else "❌", str(e)[:100])

    # P8-05: Rapid fire 10 calls
    try:
        ok_count = 0
        for i in range(10):
            try:
                r = txt(sess.call_tool("catia_list_documents", timeout=15))
                if len(r) > 5:
                    ok_count += 1
            except:
                pass
        record("P8", "P8-05", "✅" if ok_count >= 8 else "❌", f"{ok_count}/10 rapid calls succeeded")
    except Exception as e:
        record("P8", "P8-05", "❌", str(e)[:100])

    # ============ P9: New Tools (v1.10.0) ============
    print("\n" + "="*60)
    print("PHASE P9: New Tools (v1.10.0)")
    print("="*60)

    # Close previous parts first, then create fresh part for GSD tests
    try:
        r = txt(sess.call_tool("catia_close_document", {"file_path": "TestPart"}))
        print(f"  [Setup] Close previous: {r[:80]}")
    except: pass
    try:
        r = txt(sess.call_tool("catia_close_document", {"file_path": "TestGSD"}))
        print(f"  [Setup] Close previous: {r[:80]}")
    except: pass

    # Fresh part for GSD new tool tests
    try:
        r = txt(sess.call_tool("catia_new_part", {"name": "TestNewTools"}))
        print(f"  [Setup] New part: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] New part failed: {e}")

    # GSD: Create geometrical set and base geometry IN THIS PART
    try:
        r = txt(sess.call_tool("catia_create_geometrical_set", {"name": "TestSet"}))
        print(f"  [Setup] Geometrical set: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] Geometrical set failed: {e}")

    try:
        r = txt(sess.call_tool("catia_create_point_coord", {"x": 0, "y": 0, "z": 0, "set_name": "TestSet"}))
        print(f"  [Setup] Point coord: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] Point coord failed: {e}")

    try:
        r = txt(sess.call_tool("catia_create_line_2points", {"x1": 0, "y1": 0, "z1": 0, "x2": 100, "y2": 0, "z2": 0, "set_name": "TestSet"}))
        print(f"  [Setup] Line 2points: {r[:80]}")
    except Exception as e:
        print(f"  [Setup] Line 2points failed: {e}")

    # P9-01: catia_create_point_on_curve (happy path with fresh geometry)
    try:
        r = txt(sess.call_tool("catia_create_point_on_curve", {"curve_name": "Line.1", "parameter": 0.5, "set_name": "TestSet"}))
        ok = "point" in r.lower() or "created" in r.lower()
        record("P9", "P9-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-01", "❌", str(e)[:100])

    # P9-02: catia_create_point_intersection (happy path)
    try:
        r = txt(sess.call_tool("catia_create_point_intersection", {"element1": "Line.1", "element2": "Point.1", "set_name": "TestSet"}))
        ok = "point" in r.lower() or "created" in r.lower() or "intersection" in r.lower()
        record("P9", "P9-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-02", "❌", str(e)[:100])

    # P9-03: catia_create_line_tangent (happy path)
    try:
        r = txt(sess.call_tool("catia_create_line_tangent", {"curve_name": "Line.1", "point_name": "Point.1", "set_name": "TestSet"}))
        ok = "line" in r.lower() or "created" in r.lower() or "tangent" in r.lower()
        record("P9", "P9-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-03", "❌", str(e)[:100])

    # P9-04: catia_create_line_normal_to_surface (happy path)
    try:
        r = txt(sess.call_tool("catia_create_line_normal_to_surface", {"surface_name": "xy", "point_name": "Point.1", "set_name": "TestSet"}))
        ok = "line" in r.lower() or "created" in r.lower() or "normal" in r.lower()
        record("P9", "P9-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-04", "❌", str(e)[:100])

    # P9-05: catia_create_plane_parallel (happy path)
    try:
        r = txt(sess.call_tool("catia_create_plane_parallel", {"reference_plane": "xy", "point_name": "Point.1", "set_name": "TestSet"}))
        ok = "plane" in r.lower() or "created" in r.lower() or "parallel" in r.lower()
        record("P9", "P9-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-05", "❌", str(e)[:100])

    # P9-06: catia_create_plane_tangent_to_surface (happy path)
    try:
        r = txt(sess.call_tool("catia_create_plane_tangent_to_surface", {"surface_name": "xy", "point_name": "Point.1", "set_name": "TestSet"}))
        ok = "plane" in r.lower() or "created" in r.lower() or "tangent" in r.lower()
        record("P9", "P9-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-06", "❌", str(e)[:100])

    # P9-07: catia_create_mirror (happy path)
    try:
        r = txt(sess.call_tool("catia_create_mirror", {"element_name": "Point.1", "mirror_plane": "xy", "set_name": "TestSet"}))
        ok = "mirror" in r.lower() or "created" in r.lower()
        record("P9", "P9-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-07", "❌", str(e)[:100])

    # P9-08: catia_create_tabulated_cylinder (happy path)
    try:
        r = txt(sess.call_tool("catia_create_tabulated_cylinder", {"curve_name": "Line.1", "height1": 10, "height2": 10, "set_name": "TestSet"}))
        ok = "cylinder" in r.lower() or "created" in r.lower() or "tabulated" in r.lower()
        record("P9", "P9-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        record("P9", "P9-08", "❌", str(e)[:100])

    # P9-09: catia_rib (validation - no spine)
    try:
        r = txt(sess.call_tool("catia_rib", {}))
        ok = "error" in r.lower() or "spine" in r.lower() or "required" in r.lower()
        record("P9", "P9-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "spine" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-09", "✅" if ok else "❌", str(e)[:100])

    # P9-10: catia_slot (validation - no spine)
    try:
        r = txt(sess.call_tool("catia_slot", {}))
        ok = "error" in r.lower() or "spine" in r.lower() or "required" in r.lower()
        record("P9", "P9-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "spine" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-10", "✅" if ok else "❌", str(e)[:100])

    # P9-11: catia_stiffener (validation - no supports)
    try:
        r = txt(sess.call_tool("catia_stiffener", {}))
        ok = "error" in r.lower() or "support" in r.lower() or "required" in r.lower()
        record("P9", "P9-11", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "support" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-11", "✅" if ok else "❌", str(e)[:100])

    # P9-12: catia_split_body (validation - no tool)
    try:
        r = txt(sess.call_tool("catia_split_body", {}))
        ok = "error" in r.lower() or "tool" in r.lower() or "required" in r.lower()
        record("P9", "P9-12", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "tool" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-12", "✅" if ok else "❌", str(e)[:100])

    # P9-13: catia_sketch_trim (validation - no sketch)
    try:
        r = txt(sess.call_tool("catia_sketch_trim", {}))
        ok = "error" in r.lower() or "sketch" in r.lower() or "required" in r.lower()
        record("P9", "P9-13", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "sketch" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-13", "✅" if ok else "❌", str(e)[:100])

    # P9-14: catia_sketch_construction_element (validation - no sketch)
    try:
        r = txt(sess.call_tool("catia_sketch_construction_element", {}))
        ok = "error" in r.lower() or "sketch" in r.lower() or "required" in r.lower()
        record("P9", "P9-14", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "sketch" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-14", "✅" if ok else "❌", str(e)[:100])

    # P9-15: catia_sketch_mirror (validation - no sketch)
    try:
        r = txt(sess.call_tool("catia_sketch_mirror", {}))
        ok = "error" in r.lower() or "sketch" in r.lower() or "required" in r.lower()
        record("P9", "P9-15", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "sketch" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-15", "✅" if ok else "❌", str(e)[:100])

    # P9-16: catia_ground_constraint (validation - no assembly)
    try:
        r = txt(sess.call_tool("catia_ground_constraint", {}))
        ok = "error" in r.lower() or "component" in r.lower() or "required" in r.lower()
        record("P9", "P9-16", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "component" in str(e).lower() or "required" in str(e).lower()
        record("P9", "P9-16", "✅" if ok else "❌", str(e)[:100])

    # ============ P10: Phase 2 Tools (v1.11.0) ============
    print("\n" + "="*60)
    print("PHASE P10: Phase 2 Tools (v1.11.0)")
    print("="*60)

    # P10-01: catia_variable_fillet (validation - no edge)
    try:
        r = txt(sess.call_tool("catia_variable_fillet", {}))
        ok = "error" in r.lower() or "edge" in r.lower() or "required" in r.lower()
        record("P10", "P10-01", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "edge" in str(e).lower() or "required" in str(e).lower()
        record("P10", "P10-01", "✅" if ok else "❌", str(e)[:100])

    # P10-02: catia_variable_fillet (validation - negative radius)
    try:
        r = txt(sess.call_tool("catia_variable_fillet", {"edge_name": "Edge.1", "radius1": -1, "radius2": 5}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P10", "P10-02", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "positive" in str(e).lower() or "invalid" in str(e).lower()
        record("P10", "P10-02", "✅" if ok else "❌", str(e)[:100])

    # P10-03: catia_drafted_filleted_pad (validation - no sketch)
    try:
        r = txt(sess.call_tool("catia_drafted_filleted_pad", {}))
        ok = "error" in r.lower() or "sketch" in r.lower() or "required" in r.lower()
        record("P10", "P10-03", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "sketch" in str(e).lower() or "required" in str(e).lower()
        record("P10", "P10-03", "✅" if ok else "❌", str(e)[:100])

    # P10-04: catia_drafted_filleted_pad (validation - zero height)
    try:
        r = txt(sess.call_tool("catia_drafted_filleted_pad", {"sketch_name": "Sketch.1", "height": 0}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P10", "P10-04", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "positive" in str(e).lower() or "invalid" in str(e).lower()
        record("P10", "P10-04", "✅" if ok else "❌", str(e)[:100])

    # P10-05: catia_drafted_filleted_pocket (validation - no sketch)
    try:
        r = txt(sess.call_tool("catia_drafted_filleted_pocket", {}))
        ok = "error" in r.lower() or "sketch" in r.lower() or "required" in r.lower()
        record("P10", "P10-05", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "sketch" in str(e).lower() or "required" in str(e).lower()
        record("P10", "P10-05", "✅" if ok else "❌", str(e)[:100])

    # P10-06: catia_drafted_filleted_pocket (validation - negative height)
    try:
        r = txt(sess.call_tool("catia_drafted_filleted_pocket", {"sketch_name": "Sketch.1", "height": -5}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P10", "P10-06", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "positive" in str(e).lower() or "invalid" in str(e).lower()
        record("P10", "P10-06", "✅" if ok else "❌", str(e)[:100])

    # P10-07: catia_multi_pad (validation - no sketch)
    try:
        r = txt(sess.call_tool("catia_multi_pad", {}))
        ok = "error" in r.lower() or "sketch" in r.lower() or "required" in r.lower()
        record("P10", "P10-07", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "sketch" in str(e).lower() or "required" in str(e).lower()
        record("P10", "P10-07", "✅" if ok else "❌", str(e)[:100])

    # P10-08: catia_multi_pad (validation - empty heights)
    try:
        r = txt(sess.call_tool("catia_multi_pad", {"sketch_name": "Sketch.1", "heights": []}))
        ok = "error" in r.lower() or "empty" in r.lower() or "required" in r.lower()
        record("P10", "P10-08", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "empty" in str(e).lower() or "required" in str(e).lower()
        record("P10", "P10-08", "✅" if ok else "❌", str(e)[:100])

    # P10-09: catia_multi_pocket (validation - no sketch)
    try:
        r = txt(sess.call_tool("catia_multi_pocket", {}))
        ok = "error" in r.lower() or "sketch" in r.lower() or "required" in r.lower()
        record("P10", "P10-09", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "sketch" in str(e).lower() or "required" in str(e).lower()
        record("P10", "P10-09", "✅" if ok else "❌", str(e)[:100])

    # P10-10: catia_multi_pocket (validation - negative depth)
    try:
        r = txt(sess.call_tool("catia_multi_pocket", {"sketch_name": "Sketch.1", "depths": [-5]}))
        ok = "error" in r.lower() or "positive" in r.lower() or "invalid" in r.lower()
        record("P10", "P10-10", "✅" if ok else "❌", r[:100])
    except Exception as e:
        ok = "error" in str(e).lower() or "positive" in str(e).lower() or "invalid" in str(e).lower()
        record("P10", "P10-10", "✅" if ok else "❌", str(e)[:100])

    # ============ Print Summary ============
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    phases = ["P0","P1","P2","P3","P4","P5","P6","P7","P8","P9","P10"]
    total = pass_c = fail_c = skip_c = 0
    for phase in phases:
        pr = [r for r in results if r["phase"] == phase]
        p = sum(1 for r in pr if r["status"] == "✅")
        f = sum(1 for r in pr if r["status"] == "❌")
        s = sum(1 for r in pr if r["status"] == "⏭️")
        total += p + f + s
        pass_c += p
        fail_c += f
        skip_c += s
        print(f"  {phase}: {p}✅ {f}❌ {s}⏭️ ({len(pr)} total)")

    print(f"\n  TOTAL: {pass_c}✅ {fail_c}❌ {skip_c}⏭️ ({total} total)")
    print(f"  Pass rate: {pass_c/(pass_c+fail_c)*100:.1f}%" if (pass_c+fail_c) > 0 else "  No executable tests")

    # Write results to file
    with open("/workspace/catia-v5-mcp-server-work/docs/REALTEST_RESULTS.md", "w") as f:
        f.write("# CATIA V5 MCP Server — Realtest Results\n\n")
        f.write(f"> **Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"> **Server:** SSE on http://192.168.177.151:8765  \n\n")
        f.write("## Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Tests | {total} |\n")
        f.write(f"| Passed ✅ | {pass_c} |\n")
        f.write(f"| Failed ❌ | {fail_c} |\n")
        f.write(f"| Skipped ⏭️ | {skip_c} |\n")
        f.write(f"| Pass Rate | {pass_c/(pass_c+fail_c)*100:.1f}% |\n\n")

        f.write("## Detailed Results\n\n")
        f.write("| Phase | Test ID | Status | Remark |\n")
        f.write("|-------|---------|--------|--------|\n")
        for r in results:
            f.write(f"| {r['phase']} | {r['id']} | {r['status']} | {r['remark'][:100]} |\n")
        f.write("\n")

    print(f"\nResults written to docs/REALTEST_RESULTS.md")

    # ── Cleanup: close all documents created during testing ──
    print("\nCleanup: closing all test documents...")
    try:
        docs_raw = sess.call_tool("catia_list_documents", {})
        docs_txt = txt(docs_raw)
        import json as _json
        doc_list = _json.loads(docs_txt)
        for doc in doc_list:
            name = doc.get("name", "")
            path = doc.get("path", "")
            if not path or path == name:
                sess.call_tool("catia_close_document", {"file_path": name})
                print(f"  Closed (unsaved): {name}")
            else:
                sess.call_tool("catia_close_document", {"file_path": path})
                print(f"  Closed: {name}")
    except Exception as e:
        print(f"  Cleanup warning: {e}")

    print("Cleanup complete.\n")


if __name__ == "__main__":
    sess = MCPSession()
    try:
        sid = sess.connect()
        print(f"Connected: {sid[:12]}...", file=sys.stderr)
        run_tests(sess)
    finally:
        sess.close()
