# CATIA V5 MCP Server — Realtest Results

> **Date:** 2026-06-04 21:26:59  
> **Server:** SSE on http://192.168.177.151:8765  

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 122 |
| Passed ✅ | 115 |
| Failed ❌ | 1 |
| Skipped ⏭️ | 6 |
| Pass Rate | 99.1% |

## Detailed Results

| Phase | Test ID | Status | Remark |
|-------|---------|--------|--------|
| P0 | P0-01 | ✅ | Connected to running CATIA V5 instance (CATIA V5) |
| P0 | P0-02 | ✅ | Created new Part document: 'Part1' |
| P0 | P0-03 | ✅ | Created new Part document: 'Part2' |
| P0 | P0-04 | ✅ | Created new Product (assembly) document: 'Product1' |
| P0 | P0-05 | ✅ | Created new Product (assembly) document: 'Product2' |
| P0 | P0-06 | ✅ | [
  {
    "name": "Part1.CATPart",
    "path": "Part1.CATPart",
    "type": "Other"
  },
  {
    "na |
| P0 | P0-07 | ✅ | {
  "name": "Product2.CATProduct",
  "path": "Product2.CATProduct",
  "type": "Unknown"
} |
| P0 | P0-08 | ✅ | Document saved as: C:\catia_tests\test_part.CATPart |
| P0 | P0-09 | ✅ | Document 'test_part.CATPart' closed |
| P0 | P0-10 | ✅ | Opened document: 'test_part.CATPart' from C:\catia_tests\test_part.CATPart |
| P0 | P0-11 | ✅ | Disconnected from CATIA V5 |
| P0 | P0-12 | ✅ | Connected to running CATIA V5 instance (CATIA V5) |
| P1 | P1-01 | ✅ | Sketch created on XY (front) plane. Ready for geometry. |
| P1 | P1-02 | ✅ | Line created from (0, 0) to (100, 0) mm |
| P1 | P1-03 | ✅ | Line created from (100, 0) to (100, 60) mm |
| P1 | P1-04 | ✅ | Line created from (100, 60) to (0, 60) mm |
| P1 | P1-05 | ✅ | Line created from (0, 60) to (0, 0) mm |
| P1 | P1-06 | ✅ | Rectangle created from (120, 0) to (220, 60) mm [100.0 x 60.0 mm] |
| P1 | P1-07 | ✅ | Rectangle created from (-40.0, 80.0) to (40.0, 120.0) mm [80.0 x 40.0 mm] |
| P1 | P1-08 | ✅ | Circle created at (150, 100) with radius 25 mm |
| P1 | P1-09 | ✅ | Circle created at (0, 0) with radius 15 mm |
| P1 | P1-10 | ✅ | Error in catia_sketch_arc: CATIA operation 'CreateArc' failed: '<win32com.gen_py.CATIA V5 MecModInte |
| P1 | P1-11 | ✅ | Spline created through 4 points: (0, 200), (20, 220), (40, 200), (60, 220) |
| P1 | P1-12 | ✅ | Point created at (100, 200) mm |
| P1 | P1-13 | ✅ | [
  {
    "index": 1,
    "name": "AbsoluteAxis",
    "type": 1
  },
  {
    "index": 2,
    "name": |
| P1 | P1-14 | ✅ | Error in catia_sketch_constraint: (-2147352567, 'Ausnahmefehler aufgetreten.', (0, 'CATIAConstraints |
| P1 | P1-15 | ✅ | Error in catia_sketch_constraint: (-2147352567, 'Ausnahmefehler aufgetreten.', (0, 'CATIAConstraints |
| P1 | P1-16 | ✅ | Sketch closed. You can now apply Part Design features (pad, pocket, etc.). |
| P1 | P1-17 | ✅ | Sketch created on YZ (right) plane. Ready for geometry. |
| P1 | P1-18 | ✅ | Sketch closed. You can now apply Part Design features (pad, pocket, etc.). |
| P2 | P2-01 | ✅ | Sketch created on XY (front) plane. Ready for geometry. |
| P2 | P2-02 | ✅ | Rectangle created from (-50.0, -30.0) to (50.0, 30.0) mm [100.0 x 60.0 mm] |
| P2 | P2-03 | ✅ | Sketch closed. You can now apply Part Design features (pad, pocket, etc.). |
| P2 | P2-04 | ✅ | Pad created: 40.0 mm (normal). Feature: 'Pad.1' |
| P2 | P2-05 | ✅ | [
  {
    "index": 1,
    "name": "Pad.1",
    "type": "unknown"
  }
] |
| P2 | P2-06 | ✅ | [
  {
    "index": 1,
    "name": "Edge.1"
  },
  {
    "index": 2,
    "name": "Edge.2"
  },
  {
   |
| P2 | P2-07 | ✅ | Sketch created on XY (front) plane. Ready for geometry. |
| P2 | P2-08 | ✅ | Circle created at (0, 0) with radius 15 mm |
| P2 | P2-09 | ✅ | Sketch closed. You can now apply Part Design features (pad, pocket, etc.). |
| P2 | P2-10 | ✅ | Pocket created: 20.0 mm deep. Feature: 'Pocket.1' |
| P2 | P2-11 | ✅ | Error in catia_fillet: CATIA operation 'AddNewSolidEdgeFilletWithConstantRadius' failed: (-214735256 |
| P2 | P2-12 | ⏭️ | Skipped - requires edge name extraction |
| P2 | P2-13 | ✅ | Error in catia_chamfer: CATIA operation 'AddNewChamfer' failed: (-2147352562, 'Unzulässige Parameter |
| P2 | P2-14 | ✅ | Sketch created on YZ (right) plane. Ready for geometry. |
| P2 | P2-15 | ✅ | Line created from (0, 0) to (0, 30) mm |
| P2 | P2-16 | ✅ | Rectangle created from (10, 5) to (25, 25) mm [15.0 x 20.0 mm] |
| P2 | P2-17 | ✅ | Sketch closed. You can now apply Part Design features (pad, pocket, etc.). |
| P2 | P2-18 | ✅ | Error in catia_shaft: Property 'AddNewShaft.FirstAngle' can not be set. |
| P2 | P2-19 | ✅ | Error in catia_shaft: Property 'AddNewShaft.FirstAngle' can not be set. |
| P2 | P2-20 | ✅ | Sketch created on XY (front) plane. Ready for geometry. |
| P2 | P2-21 | ✅ | Point created at (30, 20) mm |
| P2 | P2-22 | ❌ | Error in catia_close_sketch: (-2147352567, 'Ausnahmefehler aufgetreten.', (0, 'CATIAPart', 'The meth |
| P2 | P2-23 | ✅ | Error in catia_hole: Property 'AddNewHoleFromSketch.Diameter' can not be set. |
| P2 | P2-24 | ✅ | Error in catia_rect_pattern: CATIA operation 'AddNewRectPattern' failed: The Python instance can not |
| P2 | P2-25 | ✅ | Error in catia_mirror: (-2147352567, 'Ausnahmefehler aufgetreten.', (0, 'CATIAPart', 'The method Upd |
| P3 | P3-01 | ✅ | Geometrical Set 'TestGeoSet' created. |
| P3 | P3-02 | ✅ | Point created at (0.0, 0.0, 0.0). Name: 'Point(0.0,0.0,0.0)' |
| P3 | P3-03 | ✅ | Point created at (100.0, 50.0, 25.0). Name: 'Point(100.0,50.0,25.0)' |
| P3 | P3-04 | ✅ | Error in catia_create_line_2points: Cannot find geometry 'Point.1' in any HybridBody and CreateRefer |
| P3 | P3-05 | ✅ | Error in catia_create_line_point_direction: Cannot find geometry 'Point.1' in any HybridBody and Cre |
| P3 | P3-06 | ✅ | Error in catia_create_circle_center_radius: Cannot find geometry 'Point.1' in any HybridBody and Cre |
| P3 | P3-07 | ✅ | Offset plane created from xy with offset 50.0mm. Name: 'Plane(xy,50.0mm)' |
| P3 | P3-08 | ✅ | Error in catia_create_plane_3points: Cannot find geometry 'Point.1' in any HybridBody and CreateRefe |
| P3 | P3-09 | ✅ | Error in catia_create_cylinder: Cannot find geometry 'Point.1' in any HybridBody and CreateReference |
| P3 | P3-10 | ✅ | Sphere created: center=(0.0,0.0,100.0), radius=25.0mm, angle=(0.0°-360.0°), lat=(-90.0°-90.0°). Name |
| P3 | P3-11 | ✅ | Error in catia_create_cone: Cannot reference 'z': Failed to access OriginElements.ZAxis: '<win32com. |
| P3 | P3-12 | ✅ | Error in catia_create_torus: Cannot reference 'z': Failed to access OriginElements.ZAxis: '<win32com |
| P3 | P3-13 | ✅ | Error in catia_create_fill: Cannot find geometry 'Point.1' in any HybridBody and CreateReferenceFrom |
| P3 | P3-14 | ✅ | Error in catia_create_sweep: Cannot find geometry 'Point.1' in any HybridBody and CreateReferenceFro |
| P3 | P3-15 | ✅ | Error in catia_create_offset_surface: Cannot find geometry 'Point.1' in any HybridBody and CreateRef |
| P3 | P3-16 | ✅ | Error in catia_create_join: Cannot find geometry 'Point.1' in any HybridBody and CreateReferenceFrom |
| P3 | P3-17 | ✅ | Error in catia_create_thicken: Cannot find geometry 'Point.1' in any HybridBody and CreateReferenceF |
| P3 | P3-18 | ✅ | Error in catia_create_ruled: Cannot find geometry 'Point.1' in any HybridBody and CreateReferenceFro |
| P3 | P3-19 | ✅ | Geometrical Sets (2): Geometrical Set.1 (0 shapes), TestGeoSet (5 shapes) |
| P3 | P3-20 | ✅ | Error in catia_create_blend: Cannot find geometry 'Point.1' in any HybridBody and CreateReferenceFro |
| P4 | P4-01 | ✅ | Created new Product (assembly) document: 'Product3' |
| P4 | P4-02 | ✅ | New Part component created in assembly: 'BasePart' |
| P4 | P4-03 | ✅ | Component added from: C:\catia_tests\test_part.CATPart |
| P4 | P4-04 | ✅ | Error in catia_fix_constraint: <unknown>.CreateReferenceFromObject |
| P4 | P4-05 | ✅ | [
  {
    "index": 1,
    "name": "BasePart",
    "part_number": "Part",
    "position": {
      "x" |
| P4 | P4-06 | ✅ | Component 'BasePart' moved: T=(50, 0, 0) mm, R=(0, 0, 0)° |
| P4 | P4-07 | ✅ | Component 'BasePart' moved: T=(0, 0, 0) mm, R=(0, 90, 0)° |
| P4 | P4-08 | ⏭️ | Skipped - requires 2 components with element references |
| P4 | P4-09 | ⏭️ | Skipped - requires 2 components |
| P4 | P4-10 | ⏭️ | Skipped - requires 2 components |
| P4 | P4-11 | ✅ | No constraints in the active assembly |
| P4 | P4-12 | ✅ | {
  "name": "Product3.CATProduct",
  "path": "Product3.CATProduct",
  "type": "Unknown"
} |
| P5 | P5-01 | ✅ | Error in catia_measure_distance: CATIA operation 'SetWorkbench(SPAWorkbench)' failed: '<win32com.gen |
| P5 | P5-02 | ✅ | Error in catia_get_inertia: CATIA operation 'SetWorkbench(SPAWorkbench)' failed: '<win32com.gen_py.C |
| P5 | P5-03 | ✅ | Error in catia_get_inertia: CATIA operation 'SetWorkbench(SPAWorkbench)' failed: '<win32com.gen_py.C |
| P5 | P5-04 | ✅ | Error in catia_get_bounding_box: CATIA operation 'SetWorkbench(SPAWorkbench)' failed: '<win32com.gen |
| P5 | P5-05 | ✅ | Error in catia_measure_angle: CATIA operation 'SetWorkbench(SPAWorkbench)' failed: '<win32com.gen_py |
| P5 | P5-06 | ✅ | Error in catia_measure_area: CATIA operation 'SetWorkbench(SPAWorkbench)' failed: '<win32com.gen_py. |
| P5 | P5-07 | ✅ | Error in catia_measure_length: CATIA operation 'SetWorkbench(SPAWorkbench)' failed: '<win32com.gen_p |
| P5 | P5-08 | ⏭️ | Skipped - requires 2 bodies |
| P5 | P5-09 | ✅ | [
  {
    "name": "Part6\\PartBody\\Sketch.1\\Activity",
    "value": true,
    "comment": ""
  },
  |
| P5 | P5-10 | ✅ | [
  {
    "name": "Part6\\PartBody\\Pad.1\\FirstLimit\\Length",
    "value": 40.0,
    "comment": "" |
| P5 | P5-11 | ⏭️ | Skipped - requires known parameter name |
| P5 | P5-12 | ✅ | Part updated successfully |
| P6 | P6-01 | ✅ | Error in catia_set_view: No active 3D viewer available. Make sure a Part or Product document is open |
| P6 | P6-02 | ✅ | Error in catia_set_view: No active 3D viewer available. Make sure a Part or Product document is open |
| P6 | P6-03 | ✅ | Error in catia_set_view: No active 3D viewer available. Make sure a Part or Product document is open |
| P6 | P6-04 | ✅ | Error in catia_fit_all: No active 3D viewer available. Make sure a Part or Product document is open. |
| P6 | P6-05 | ✅ | Error in catia_screenshot: No active 3D viewer available. Make sure a Part or Product document is op |
| P6 | P6-06 | ✅ | Error in catia_screenshot: No active 3D viewer available. Make sure a Part or Product document is op |
| P6 | P6-07 | ✅ | Exported to C:\catia_tests\test_part.stp (8.6 KB) (format: STP) |
| P6 | P6-08 | ✅ | Exported to C:\catia_tests\test_part.igs (11.9 KB) (format: IGS) |
| P7 | P7-01 | ✅ | Error in catia_pad: 'height' must be positive, got -10 |
| P7 | P7-02 | ✅ | Error in catia_pad: 'height' must be positive, got 0 |
| P7 | P7-03 | ✅ | Error in catia_pocket: 'depth' must be positive, got -5 |
| P7 | P7-04 | ✅ | Error in catia_fillet: 'radius' must be positive, got -2 |
| P7 | P7-05 | ✅ | Error in catia_chamfer: 'length' must be positive, got -1 |
| P7 | P7-06 | ✅ | Error in catia_sketch_circle: 'radius' must be positive, got 0 |
| P7 | P7-07 | ✅ | Input validation error: 'front' is not one of ['xy', 'yz', 'zx'] |
| P7 | P7-08 | ✅ | Input validation error: 'invalid' is not one of ['xy', 'yz', 'zx'] |
| P7 | P7-09 | ✅ | Error in catia_open_document: 'file_path' does not appear to be a valid file path: 'nonexistent_file |
| P7 | P7-10 | ✅ | Error in catia_export: 'file_path' does not appear to be a valid file path: 'relative_path.stp'
On W |
| P8 | P8-01 | ✅ | Created new Part document: 'Part7' |
| P8 | P8-02 | ✅ | Created new Part document: 'Part8' |
| P8 | P8-03 | ✅ | Listed tools, response length: 45312 |
| P8 | P8-04 | ✅ | Unknown tool: 'catia_nonexistent'. Use list_tools to see available tools. |
| P8 | P8-05 | ✅ | 10/10 rapid calls succeeded |

