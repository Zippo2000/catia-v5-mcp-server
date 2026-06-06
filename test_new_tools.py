"""Quick live test of new tools via MCP SSE on Windows."""
import requests
import sseclient
import json

SSE_URL = "http://192.168.177.151:8765/sse"
MSG_URL = "http://192.168.177.151:8765/messages/"

class MCPSession:
    def __init__(self):
        self.session_id = None
        self.s = requests.Session()
        self.connect()
    
    def connect(self):
        resp = self.s.get(SSE_URL, stream=True, timeout=120)
        client = sseclient.SSEClient(resp)
        for ev in client.events():
            if ev.event == 'endpoint':
                self.session_id = ev.data.split('/')[-1]
                return
    
    def call_tool(self, tool_name, arguments=None):
        if arguments is None:
            arguments = {}
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        resp = self.s.post(f"{MSG_URL}{self.session_id}", json=payload, timeout=30)
        client = sseclient.SSEClient(resp)
        results = []
        for ev in client.events():
            if ev.data:
                results.append(json.loads(ev.data))
        return results

def txt(results):
    for r in results:
        for c in r.get("content", []):
            if c.get("type") == "text":
                return c["text"]
    return ""

print("=== Connecting to MCP Server ===")
sess = MCPSession()
print(f"Session: {sess.session_id}")

# Connect to CATIA
print("\n=== P0: catia_connect ===")
r = txt(sess.call_tool("catia_connect"))
print(r[:200])

# Create new part
print("\n=== P0: catia_new_part ===")
r = txt(sess.call_tool("catia_new_part", {"name": "TestNewTools"}))
print(r[:200])

# ---- GSD: Create geometrical set ----
print("\n=== GSD: catia_create_geometrical_set ===")
r = txt(sess.call_tool("catia_create_geometrical_set", {"name": "TestSet"}))
print(r[:200])

# ---- GSD: Create point coord ----
print("\n=== GSD: catia_create_point_coord ===")
r = txt(sess.call_tool("catia_create_point_coord", {"x": 0, "y": 0, "z": 0}))
print(r[:200])

# ---- GSD: Create line 2points ----
print("\n=== GSD: catia_create_line_2points ===")
r = txt(sess.call_tool("catia_create_line_2points", {"x1": 0, "y1": 0, "z1": 0, "x2": 100, "y2": 0, "z2": 0}))
print(r[:200])

# ---- GSD: catia_create_point_on_curve (NEW!) ----
print("\n=== NEW: catia_create_point_on_curve ===")
r = txt(sess.call_tool("catia_create_point_on_curve", {"curve_name": "Line.1", "parameter": 0.5, "set_name": "TestSet"}))
print(r[:200])

# ---- GSD: catia_create_point_intersection (NEW!) ----
print("\n=== NEW: catia_create_point_intersection ===")
r = txt(sess.call_tool("catia_create_point_intersection", {"element1": "Line.1", "element2": "Point.1", "set_name": "TestSet"}))
print(r[:200])

# ---- GSD: catia_create_line_tangent (NEW!) ----
print("\n=== NEW: catia_create_line_tangent ===")
r = txt(sess.call_tool("catia_create_line_tangent", {"curve_name": "Line.1", "point_name": "Point.1", "set_name": "TestSet"}))
print(r[:200])

# ---- GSD: catia_create_plane_parallel (NEW!) ----
print("\n=== NEW: catia_create_plane_parallel ===")
r = txt(sess.call_tool("catia_create_plane_parallel", {"reference_plane": "xy", "point_name": "Point.1", "set_name": "TestSet"}))
print(r[:200])

# ---- GSD: catia_create_mirror (NEW!) ----
print("\n=== NEW: catia_create_mirror ===")
r = txt(sess.call_tool("catia_create_mirror", {"element_name": "Point.1", "mirror_plane": "xy", "set_name": "TestSet"}))
print(r[:200])

# ---- GSD: catia_create_tabulated_cylinder (NEW!) ----
print("\n=== NEW: catia_create_tabulated_cylinder ===")
r = txt(sess.call_tool("catia_create_tabulated_cylinder", {"curve_name": "Line.1", "height1": 10, "height2": 10, "set_name": "TestSet"}))
print(r[:200])

# ---- Part Design: catia_rib (NEW!) ----
print("\n=== NEW: catia_rib (validation - no spine) ===")
r = txt(sess.call_tool("catia_rib", {}))
print(r[:200])

# ---- Part Design: catia_split_body (NEW!) ----
print("\n=== NEW: catia_split_body (validation - no tool) ===")
r = txt(sess.call_tool("catia_split_body", {}))
print(r[:200])

# ---- Sketcher: catia_sketch_trim (NEW!) ----
print("\n=== NEW: catia_sketch_trim (validation - no sketch) ===")
r = txt(sess.call_tool("catia_sketch_trim", {}))
print(r[:200])

# ---- Sketcher: catia_sketch_construction_element (NEW!) ----
print("\n=== NEW: catia_sketch_construction_element (validation - no sketch) ===")
r = txt(sess.call_tool("catia_sketch_construction_element", {}))
print(r[:200])

# ---- Assembly: catia_ground_constraint (NEW!) ----
print("\n=== NEW: catia_ground_constraint (validation - no assembly) ===")
r = txt(sess.call_tool("catia_ground_constraint", {}))
print(r[:200])

print("\n=== Done ===")
