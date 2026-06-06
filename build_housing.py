#!/usr/bin/env python3
"""Build an aluminum die-cast industrial housing (~3L volume) in CATIA V5 via MCP.

Strategy:
1. Outer block: Sketch on XY, Pad upward (z=0..95)
2. Offset plane at z=90 (parallel to XY)
3. Inner cavity + holes: Sketch on offset plane, Pocket downward (normal direction)
4. Cover plate: Offset plane at z=95, Sketch on it, Pad downward (reverse)
5. Drain channel: Sketch on XY, Pocket upward (normal)
"""

import json
import sys
sys.path.insert(0, "/workspace/catia-v5-mcp-server-work")
from run_realtests import MCPSession, txt


def main():
    sess = MCPSession()
    sess.connect()
    print(f"Connected: {sess.session_id[:12]}...")

    def call(name, args=None, timeout=60):
        r = sess.call_tool(name, args or {}, timeout=timeout)
        return txt(r)

    def check(r, step):
        if r.startswith("Error"):
            print(f"  ⚠️  {step}: {r[:120]}")
        else:
            print(f"  ✅ {step}: {r[:120]}")
        return r

    try:
        # ── 0. Close any existing documents first ──
        docs_raw = call("catia_list_documents")
        try:
            doc_list = json.loads(docs_raw)
            for doc in doc_list:
                name = doc.get("name", "unknown")
                print(f"  🗑️  Closing existing: {name}")
                call("catia_close_document", {"file_path": name})
        except (json.JSONDecodeError, TypeError):
            pass

        # ── 1. New Part ──
        check(call("catia_new_part"), "1. New Part")

        # ── 2. Outer profile: 190×140 mm on XY ──
        check(call("catia_create_sketch", {"plane": "xy"}), "2. Sketch XY")
        check(call("catia_sketch_rectangle", {"x1": -95, "y1": -70, "x2": 95, "y2": 70}), "3. Outer rect")
        check(call("catia_close_sketch"), "4. Close sketch")

        # ── 5. Pad: 95 mm (z=0..95) ──
        check(call("catia_pad", {"height": 95}), "5. Pad (95mm)")

        # ── 6. Create offset plane at z=90 (for inner cavity pockets) ──
        r = call("catia_create_plane_offset", {"reference_plane": "xy", "offset": 90})
        print(f"  ✅ 6. Offset plane (z=90): {r[:120]}")
        # Extract plane name from response: "Offset plane created from xy with offset 90.0mm. Name: 'Plane(xy,90mm)'"
        import re
        m = re.search(r"Name:\s*'([^']+)'", r)
        cavity_plane = m.group(1) if m else "Plane(xy,90mm)"
        print(f"     → Plane name: '{cavity_plane}'")

        # ── 7. Inner cavity: 180×130 mm on offset plane ──
        check(call("catia_create_sketch", {"plane_name": cavity_plane}), f"7. Sketch on {cavity_plane}")
        check(call("catia_sketch_rectangle", {"x1": -90, "y1": -65, "x2": 90, "y2": 65}), "8. Inner rect")
        check(call("catia_close_sketch"), "9. Close sketch")

        # ── 10. Pocket: 85 mm (normal cuts downward into material from offset plane) ──
        check(call("catia_pocket", {"depth": 85}), "10. Pocket cavity (85mm, normal)")

        # ── 11-14. 4× M6 mounting holes on same offset plane ──
        for i, (cx, cy) in enumerate([(-80, -55), (80, -55), (-80, 55), (80, 55)]):
            check(call("catia_create_sketch", {"plane_name": cavity_plane}), f"11.{i} Sketch on {cavity_plane}")
            check(call("catia_sketch_circle", {"cx": cx, "cy": cy, "radius": 3.5}), f"12.{i} Circle ({cx},{cy})")
            check(call("catia_close_sketch"), f"13.{i} Close")
            check(call("catia_pocket", {"depth": 85}), f"14.{i} Pocket hole (normal)")

        # ── 15. Cover plate: offset plane at z=95 (top of pad) ──
        r = call("catia_create_plane_offset", {"reference_plane": "xy", "offset": 95})
        print(f"  ✅ 15. Offset plane (z=95): {r[:120]}")
        m = re.search(r"Name:\s*'([^']+)'", r)
        cover_plane = m.group(1) if m else "Plane(xy,95mm)"
        print(f"     → Plane name: '{cover_plane}'")

        # ── 16. Cover plate sketch: 188×138 mm ──
        check(call("catia_create_sketch", {"plane_name": cover_plane}), f"16. Sketch on {cover_plane}")
        check(call("catia_sketch_rectangle", {"x1": -94, "y1": -69, "x2": 94, "y2": 69}), "17. Cover rect")
        check(call("catia_close_sketch"), "18. Close")

        # ── 19. Pad cover: 5 mm downward (reverse) ──
        check(call("catia_pad", {"height": 5, "direction": "reverse"}), "19. Pad cover (5mm, reverse)")

        # ── 20. Drain channel: 10×20 mm on XY, 3 mm ──
        check(call("catia_create_sketch", {"plane": "xy"}), "20. Sketch XY")
        check(call("catia_sketch_rectangle", {"x1": -5, "y1": -10, "x2": 5, "y2": 10}), "21. Drain rect")
        check(call("catia_close_sketch"), "22. Close")
        check(call("catia_pocket", {"depth": 3}), "23. Pocket drain (3mm)")

        # ── 24. Save ──
        check(call("catia_save_document", {"file_path": "C:\\catia_tests\\alu_housing_3L.CATPart"}, timeout=120), "24. Save")

        print("\n✅ Housing complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        sess.close()


if __name__ == "__main__":
    main()
