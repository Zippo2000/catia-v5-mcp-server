#!/usr/bin/env python3
"""MCP SSE client for CATIA V5 Realtests with proper init handshake."""
import json, re, sys, threading, time
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
        self._client = None
        self._initialized = False

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

        # MCP initialize handshake
        self._do_init()
        return self.session_id

    def _do_init(self):
        url = f"{MSG_URL}?session_id={self.session_id}"
        init = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hermes-test", "version": "1.0"}
            }
        }
        r = requests.post(url, json=init, timeout=30)
        r.raise_for_status()
        # Wait for init response via SSE
        deadline = time.time() + 15
        while time.time() < deadline:
            with self._lock:
                if "init-1" not in self._pending:
                    self._initialized = True
                    return
            time.sleep(0.1)
        # Even if we didn't get init response, try to proceed
        # Some servers don't send init response over SSE
        self._initialized = True

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
        rid = f"call-{id(self)}-{time.time()}"
        import uuid as _uuid
        rid = str(_uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": "tools/call",
            "params": {"name": name, "arguments": args},
        }
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
                    if isinstance(result, dict) and "error" in result:
                        msg = result["error"].get("message", "Unknown error")
                        raise RuntimeError(f"MCP Error: {msg}")
                    return result
            time.sleep(0.05)
        with self._lock:
            self._pending.pop(rid, None)
        raise RuntimeError(f"Timeout: no response for {name}")

    def list_tools(self, timeout=30):
        import uuid as _uuid
        rid = str(_uuid.uuid4())
        payload = {"jsonrpc": "2.0", "id": rid, "method": "tools/list", "params": {}}
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
            try:
                self._resp.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=3)


def txt(result):
    if "error" in result:
        e = result["error"]
        return f"ERROR: {e.get('code','?')} - {e.get('message','Unknown')}"
    parts = [i.get("text","") for i in result.get("result",{}).get("content",[]) if i.get("type")=="text"]
    return "\n".join(parts) if parts else str(result)


def run(cmd, args):
    sess = MCPSession()
    try:
        sid = sess.connect()
        print(f"Session: {sid[:12]}...", file=sys.stderr)

        if cmd == "connect":
            print(txt(sess.call_tool("catia_connect")))
        elif cmd == "disconnect":
            print(txt(sess.call_tool("catia_disconnect")))
        elif cmd == "close":
            print(txt(sess.call_tool("catia_close")))
        elif cmd == "new_part":
            print(txt(sess.call_tool("catia_new_part", {"name": args[0]} if args else {})))
        elif cmd == "new_product":
            print(txt(sess.call_tool("catia_new_product", {"name": args[0]} if args else {})))
        elif cmd == "list_documents":
            print(txt(sess.call_tool("catia_list_documents")))
        elif cmd == "get_active_doc":
            print(txt(sess.call_tool("catia_get_active_document_info")))
        elif cmd == "save":
            print(txt(sess.call_tool("catia_save_document", {"file_path": args[0]} if args else {})))
        elif cmd == "close_doc":
            print(txt(sess.call_tool("catia_close_document", {"save": args[0].lower()=="true" if args else False})))
        elif cmd == "open":
            print(txt(sess.call_tool("catia_open_document", {"file_path": args[0]})))
        elif cmd == "create_sketch":
            print(txt(sess.call_tool("catia_create_sketch", {"plane": args[0] if args else "xy"})))
        elif cmd == "close_sketch":
            print(txt(sess.call_tool("catia_close_sketch")))
        elif cmd == "sketch_line":
            print(txt(sess.call_tool("catia_sketch_line", {"x1":float(args[0]),"y1":float(args[1]),"x2":float(args[2]),"y2":float(args[3])})))
        elif cmd == "sketch_rectangle":
            print(txt(sess.call_tool("catia_sketch_rectangle", {"x1":float(args[0]),"y1":float(args[1]),"x2":float(args[2]),"y2":float(args[3])})))
        elif cmd == "sketch_centered_rectangle":
            print(txt(sess.call_tool("catia_sketch_centered_rectangle", {"cx":float(args[0]),"cy":float(args[1]),"width":float(args[2]),"height":float(args[3])})))
        elif cmd == "sketch_circle":
            p = {"radius":float(args[0])}
            if len(args)>=3: p["cx"]=float(args[1]); p["cy"]=float(args[2])
            print(txt(sess.call_tool("catia_sketch_circle", p)))
        elif cmd == "sketch_arc":
            print(txt(sess.call_tool("catia_sketch_arc", {"cx":float(args[0]),"cy":float(args[1]),"radius":float(args[2]),"start_angle":float(args[3]),"end_angle":float(args[4])})))
        elif cmd == "sketch_spline":
            pts = [[float(x) for x in m.group(1).split(",")] for m in re.finditer(r'\[([^\]]+)\]', args[0])]
            print(txt(sess.call_tool("catia_sketch_spline", {"points":pts})))
        elif cmd == "sketch_point":
            print(txt(sess.call_tool("catia_sketch_point", {"x":float(args[0]),"y":float(args[1])})))
        elif cmd == "get_geometry":
            print(txt(sess.call_tool("catia_sketch_get_geometry")))
        elif cmd == "constraint":
            p = {"type":args[0],"geometry_index_1":int(args[1])}
            if len(args)>2: p["geometry_index_2"]=int(args[2])
            if len(args)>3: p["value"]=float(args[3])
            print(txt(sess.call_tool("catia_sketch_constraint", p)))
        elif cmd == "pad":
            print(txt(sess.call_tool("catia_pad", {"height":float(args[0])})))
        elif cmd == "pocket":
            print(txt(sess.call_tool("catia_pocket", {"depth":float(args[0])})))
        elif cmd == "fillet":
            p = {"radius":float(args[0])}
            if len(args)>1: p["edge_name"]=args[1]
            print(txt(sess.call_tool("catia_fillet", p)))
        elif cmd == "chamfer":
            p = {"length":float(args[0])}
            if len(args)>1: p["angle"]=float(args[1])
            print(txt(sess.call_tool("catia_chamfer", p)))
        elif cmd == "shaft":
            print(txt(sess.call_tool("catia_shaft", {"angle":float(args[0])})))
        elif cmd == "hole":
            print(txt(sess.call_tool("catia_hole", {"diameter":float(args[0]),"depth":float(args[1])})))
        elif cmd == "rect_pattern":
            print(txt(sess.call_tool("catia_rect_pattern", {"dir1_count":int(args[0]),"dir1_spacing":float(args[1])})))
        elif cmd == "mirror":
            print(txt(sess.call_tool("catia_mirror", {"plane":args[0]})))
        elif cmd == "list_features":
            print(txt(sess.call_tool("catia_list_features")))
        elif cmd == "list_edges":
            print(txt(sess.call_tool("catia_list_edges")))
        elif cmd == "create_set":
            print(txt(sess.call_tool("catia_create_geometrical_set", {"name":args[0]})))
        elif cmd == "create_point":
            p = {"x":float(args[0]),"y":float(args[1]),"z":float(args[2])}
            if len(args)>3: p["set_name"]=args[3]
            print(txt(sess.call_tool("catia_create_point_coord", p)))
        elif cmd == "create_line_2points":
            p = {"point1_name":args[0],"point2_name":args[1]}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_line_2points", p)))
        elif cmd == "create_line_pt_dir":
            p = {"point_name":args[0],"direction":args[1]}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_line_point_direction", p)))
        elif cmd == "create_circle":
            p = {"center_name":args[0],"radius":float(args[1]),"support_plane":args[2]}
            if len(args)>3: p["set_name"]=args[3]
            print(txt(sess.call_tool("catia_create_circle_center_radius", p)))
        elif cmd == "create_plane_offset":
            p = {"reference_plane":args[0],"offset":float(args[1])}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_plane_offset", p)))
        elif cmd == "create_plane_3points":
            p = {"point1_name":args[0],"point2_name":args[1],"point3_name":args[2]}
            if len(args)>3: p["set_name"]=args[3]
            print(txt(sess.call_tool("catia_create_plane_3points", p)))
        elif cmd == "create_cylinder":
            p = {"center_name":args[0],"axis":args[1],"radius":float(args[2]),"height":float(args[3])}
            if len(args)>4: p["set_name"]=args[4]
            print(txt(sess.call_tool("catia_create_cylinder", p)))
        elif cmd == "create_sphere":
            p = {"cx":float(args[0]),"cy":float(args[1]),"cz":float(args[2]),"radius":float(args[3])}
            if len(args)>4: p["set_name"]=args[4]
            print(txt(sess.call_tool("catia_create_sphere", p)))
        elif cmd == "create_cone":
            p = {"cx":float(args[0]),"cy":float(args[1]),"cz":float(args[2]),"base_radius":float(args[3]),"height":float(args[4])}
            if len(args)>5: p["set_name"]=args[5]
            print(txt(sess.call_tool("catia_create_cone", p)))
        elif cmd == "create_torus":
            p = {"cx":float(args[0]),"cy":float(args[1]),"cz":float(args[2]),"major_radius":float(args[3]),"minor_radius":float(args[4])}
            if len(args)>5: p["set_name"]=args[5]
            print(txt(sess.call_tool("catia_create_torus", p)))
        elif cmd == "create_fill":
            p = {"contour_names":args[0].split(",")}
            if len(args)>1: p["set_name"]=args[1]
            print(txt(sess.call_tool("catia_create_fill", p)))
        elif cmd == "create_sweep":
            p = {"spine_name":args[0],"section_name":args[1]}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_sweep", p)))
        elif cmd == "create_offset_surface":
            p = {"surface_name":args[0],"distance":float(args[1])}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_offset_surface", p)))
        elif cmd == "create_join":
            p = {"surface_names":args[0].split(",")}
            if len(args)>1: p["set_name"]=args[1]
            print(txt(sess.call_tool("catia_create_join", p)))
        elif cmd == "create_thicken":
            p = {"surface_name":args[0],"thickness":float(args[1])}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_thicken", p)))
        elif cmd == "create_ruled":
            p = {"profile1":args[0],"profile2":args[1]}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_ruled", p)))
        elif cmd == "create_blend":
            p = {"edge_or_curve_name":args[0],"radius":float(args[1])}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_create_blend", p)))
        elif cmd == "split_surface":
            p = {"surface_name":args[0],"tool_name":args[1]}
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_split_surface", p)))
        elif cmd == "extend_surface":
            p = {"surface_name":args[0]}
            if len(args)>1: p["distance"]=float(args[1])
            if len(args)>2: p["set_name"]=args[2]
            print(txt(sess.call_tool("catia_extend_surface", p)))
        elif cmd == "trim_surface":
            p = {"surface_name":args[0],"tool_name":args[1]}
            if len(args)>2: p["keep_part"]=args[2]
            if len(args)>3: p["set_name"]=args[3]
            print(txt(sess.call_tool("catia_trim_surface", p)))
        elif cmd == "list_sets":
            print(txt(sess.call_tool("catia_list_geometrical_sets")))
        elif cmd == "measure_distance":
            print(txt(sess.call_tool("catia_measure_distance", {"element1":args[0],"element2":args[1]})))
        elif cmd == "get_inertia":
            p = {"density":float(args[0])} if args else {}
            print(txt(sess.call_tool("catia_get_inertia", p)))
        elif cmd == "get_bounding_box":
            print(txt(sess.call_tool("catia_get_bounding_box")))
        elif cmd == "measure_angle":
            print(txt(sess.call_tool("catia_measure_angle", {"element1":args[0],"element2":args[1]})))
        elif cmd == "measure_area":
            print(txt(sess.call_tool("catia_measure_area", {"element":args[0]})))
        elif cmd == "measure_length":
            print(txt(sess.call_tool("catia_measure_length", {"element":args[0]})))
        elif cmd == "measure_interference":
            print(txt(sess.call_tool("catia_measure_interference", {"element1":args[0],"element2":args[1]})))
        elif cmd == "get_parameters":
            p = {"filter":args[0]} if args else {}
            print(txt(sess.call_tool("catia_get_parameters", p)))
        elif cmd == "set_parameter":
            print(txt(sess.call_tool("catia_set_parameter", {"name":args[0],"value":float(args[1])})))
        elif cmd == "update_part":
            print(txt(sess.call_tool("catia_update_part")))
        elif cmd == "set_view":
            print(txt(sess.call_tool("catia_set_view", {"view":args[0]})))
        elif cmd == "fit_all":
            print(txt(sess.call_tool("catia_fit_all")))
        elif cmd == "screenshot":
            p = {"file_path":args[0]}
            if len(args)>1: p["width"]=int(args[1])
            if len(args)>2: p["height"]=int(args[2])
            print(txt(sess.call_tool("catia_screenshot", p)))
        elif cmd == "export":
            print(txt(sess.call_tool("catia_export", {"file_path":args[0]})))
        elif cmd == "add_component":
            print(txt(sess.call_tool("catia_add_component", {"file_path":args[0]})))
        elif cmd == "add_new_part":
            p = {"name":args[0]} if args else {}
            print(txt(sess.call_tool("catia_add_new_part", p)))
        elif cmd == "fix_constraint":
            print(txt(sess.call_tool("catia_fix_constraint", {"component_name":args[0]})))
        elif cmd == "move_component":
            p = {"component_name":args[0]}
            for i,k in enumerate(["tx","ty","tz","rx","ry","rz"]):
                if i+1<len(args): p[k]=float(args[i+1])
            print(txt(sess.call_tool("catia_move_component", p)))
        elif cmd == "list_components":
            print(txt(sess.call_tool("catia_list_components")))
        elif cmd == "list_constraints":
            print(txt(sess.call_tool("catia_list_constraints")))
        elif cmd == "list_tools":
            print(txt(sess.list_tools()))
        elif cmd == "call_tool":
            a = json.loads(args[1]) if len(args)>1 else {}
            print(txt(sess.call_tool(args[0], a)))
        else:
            print(f"Unknown: {cmd}", file=sys.stderr); sys.exit(1)
    finally:
        sess.close()


if __name__ == "__main__":
    if len(sys.argv)<2:
        print("Usage: python mcp_client.py <cmd> [args...]", file=sys.stderr); sys.exit(1)
    run(sys.argv[1], sys.argv[2:])
