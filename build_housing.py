#!/usr/bin/env python3
"""Build an aluminum die-cast industrial housing (~3L volume) in CATIA V5 via MCP.

Strategy:
1. Outer block: Sketch on XY, Pad upward (z=0..95)
2. Shell: Hollow out with 5mm wall thickness (full shell, no openings)
3. 4× M6 mounting holes on bottom (XY), Pocket upward
4. Cover plate: Sketch on XY, Pad upward (5mm)
5. Drain channel: Sketch on XY, Pocket upward (3mm)
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

        # ── 6. Shell: 5mm wall thickness ──
        check(call("catia_shell", {"thickness": 5}), "6. Shell (5mm)")

        # ── 7. 4× M6 mounting holes on bottom (XY) ──
        for i, (cx, cy) in enumerate([(-80, -55), (80, -55), (-80, 55), (80, 55)]):
            check(call("catia_create_sketch", {"plane": "xy"}), f"7.{i} Sketch")
            check(call("catia_sketch_circle", {"cx": cx, "cy": cy, "radius": 3.5}), f"8.{i} Circle ({cx},{cy})")
            check(call("catia_close_sketch"), f"9.{i} Close")
            check(call("catia_pocket", {"depth": 85}), f"10.{i} Pocket hole")

        # ── 11. Cover plate: 188×138 mm, 5 mm ──
        check(call("catia_create_sketch", {"plane": "xy"}), "11. Sketch XY")
        check(call("catia_sketch_rectangle", {"x1": -94, "y1": -69, "x2": 94, "y2": 69}), "12. Cover rect")
        check(call("catia_close_sketch"), "13. Close")
        check(call("catia_pad", {"height": 5}), "14. Pad cover (5mm)")

        # ── 15. Drain channel: 10×20 mm, 3 mm ──
        check(call("catia_create_sketch", {"plane": "xy"}), "15. Sketch XY")
        check(call("catia_sketch_rectangle", {"x1": -5, "y1": -10, "x2": 5, "y2": 10}), "16. Drain rect")
        check(call("catia_close_sketch"), "17. Close")
        check(call("catia_pocket", {"depth": 3}), "18. Pocket drain (3mm)")

        # ── 19. Save ──
        check(call("catia_save_document", {"file_path": "C:\\catia_tests\\alu_housing_3L.CATPart"}, timeout=180), "19. Save")

        print("\n✅ Housing complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        sess.close()


if __name__ == "__main__":
    main()
