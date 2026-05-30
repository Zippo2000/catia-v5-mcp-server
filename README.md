# CATIA V5 MCP Server

> Connect AI to Dassault Systèmes CATIA V5 via the Model Context Protocol (MCP).

The first open-source MCP server for CATIA V5. Drive CATIA V5 CAD modeling from Claude Desktop, Claude Code, LM Studio, vLLM.rs, or any other MCP-compatible client using natural language.

## What it does

This MCP server exposes **55 tools** across 6 modules that let an LLM-driven client:

| Category | Tools | Examples |
|----------|-------|----------|
| 📄 **Document Management** | 10 | Create/open/save/close parts and assemblies, list documents |
| ✏️ **2D Sketching** | 11 | Lines, rectangles, circles, arcs, splines, points, constraints |
| 🔧 **Part Design** | 15 | Pad, pocket, shaft, groove, fillet, chamfer, hole, patterns, shell, draft |
| 📦 **Assembly** | 9 | Add components, constraints (fix/coincidence/offset/angle), move |
| 📏 **Measurement** | 6 | Distance, inertia, bounding box, parameters, update |
| 📤 **Export & View** | 4 | STEP/IGES/STL export, screenshots, view orientations |

### Requirements

- **Windows** (COM automation is Windows-only)
- **CATIA V5** R2016+ installed and licensed
- **Python 3.10+**
- **Claude Desktop**, **Claude Code**, or **LM Studio** (see below)

## Installation

### Option 1: Automated setup (Recommended)

```bash
git clone https://github.com/Zippo2000/catia-v5-mcp-server.git
cd catia-v5-mcp-server
bash setup.sh
```

The `setup.sh` script handles virtual environment creation and dependency installation.

### Option 2: Manual installation

```bash
git clone https://github.com/Zippo2000/catia-v5-mcp-server.git
cd catia-v5-mcp-server

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # WSL/Linux

# Install the package
pip install -e .
```

### Option 3: Install via pip

```bash
pip install git+https://github.com/Zippo2000/catia-v5-mcp-server.git
```

## Configuration

### Claude Desktop

Edit your Claude Desktop config file:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the server entry:

```json
{
  "mcpServers": {
    "catia-v5": {
      "command": "python",
      "args": ["-m", "catia_mcp"]
    }
  }
}
```

Or with an absolute path to the project:

```json
{
  "mcpServers": {
    "catia-v5": {
      "command": "C:\\path\\to\\catia-v5-mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["-m", "catia_mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add catia-v5 python -- -m catia_mcp
```

### LM Studio (with remote vLLM or other local LLM)

**This setup lets you use the CATIA MCP Server with any local LLM running on another machine (e.g. vLLM on a Linux server), using LM Studio as the bridge.**

```
┌─────────────────────────────────────────┐
│           Windows Client                │
│                                         │
│  LM Studio (Browser-Interface)          │
│       │                                 │
│       ├── SSE ──→ catia_mcp :8765       │
│       │              │ COM              │
│       │              ▼                  │
│       │          CATIA V5               │
│       │                                 │
│       └── OpenAI API ──→ <vllm-server>:8010
│                                   │
└────────────────────────┬───────────┘
                         │ LAN
              ┌──────────▼──────────┐
              │    Linux Server     │
              │    vLLM :8010       │
              │  Qwen3.6-27B-INT4   │
              └─────────────────────┘
```

**Step 1: Start the MCP server in SSE mode on Windows**

```bash
# In your activated virtual environment:
python -m catia_mcp --sse --host 0.0.0.0 --port 8765
```

The server will output:
```
INFO:     Started server process [1234]
INFO:     Waiting for connections at http://0.0.0.0:8765/sse
```

Leave this terminal window open — the server runs in the foreground.

> **Firewall note:** If Windows Firewall blocks incoming connections on port 8765, allow the port:
> ```powershell
> New-NetFirewallRule -DisplayName "catia_mcp SSE" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
> ```

**Step 2: Configure LM Studio**

1. Open LM Studio and navigate to **Local Server** → **MCP Tools** (left sidebar)

2. **Add the MCP server:**
   - **Name:** `catia-v5`
   - **Type:** `SSE`
   - **URL:** `http://localhost:8765/sse`

3. Configure the **LLM backend:**
   - Go to **Local Server** → **Settings**
   - **LLM Provider:** `Remote OpenAI-compatible`
   - **Base URL:** `http://<vllm-server-ip>:8010/v1`
   - **Model:** `Qwen3.6-27B-AutoRound-INT4` (or whatever your vLLM serves)
   - **API Key:** (leave empty if vLLM doesn't require one)

4. Click **Start Server** and open the chat interface

5. Start chatting — LM Studio will route tool calls to CATIA via SSE and LLM responses via vLLM

**SSE server CLI options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--sse` | — | Start in SSE transport mode instead of stdio |
| `--host` | `0.0.0.0` | Bind address (use `0.0.0.0` for LAN access) |
| `--port` | `8765` | Port number for the SSE HTTP server |
| `--stdio` | — | Explicit stdio mode (default; for Claude Desktop/Code) |

> **Note:** The SSE server binds to `0.0.0.0` by default, making it accessible from other machines on your LAN. If you want local-only access, use `--host 127.0.0.1`.

### Standalone (for testing)

```bash
python -m catia_mcp
# or
catia-mcp
```

## Getting Started

1. **Start CATIA V5** — make sure it is running before using the server. The server will auto-connect to a running instance or attempt to launch one.

2. **Start the server:**

   - **Claude Desktop / Claude Code**: The server starts automatically via stdio
   - **LM Studio / remote LLM**: Run `python -m catia_mcp --sse` (see Configuration section above)

3. **Open your client** and ask the LLM to work with CATIA.

4. **Start with `catia_connect`** — the model will call this automatically when needed.

## Usage Examples

### Create a simple block

> "Create a new CATIA part. Draw a 100×60 mm rectangle centered at the origin on the XY plane, then extrude it 40 mm."

The model will call:
```
catia_new_part()
catia_create_sketch(plane="xy")
catia_sketch_centered_rectangle(cx=0, cy=0, width=100, height=60)
catia_close_sketch()
catia_pad(height=40)
```

### Design a bracket

> "Design a mounting bracket: 120×80 mm base plate, 5 mm thick. Add 4 M6 mounting holes at the corners (10 mm edge distance). Add two vertical ribs, 30 mm tall."

### Parametric modification

> "Show me all parameters of the active part. Then change the pad height to 60 mm."

### Export for manufacturing

> "Export the current part to STEP format at `C:/export/bracket.stp` and take a screenshot of the isometric view."

### Assembly

> "Create a new assembly. Add the bracket from `C:/parts/bracket.CATPart` and the base from `C:/parts/base.CATPart`. Fix the base, then create a coincidence constraint between the two."

## Architecture

```
catia-v5-mcp-server/
├── catia_mcp/
│   ├── __init__.py
│   ├── __main__.py            # python -m catia_mcp entry point
│   ├── server.py              # MCP Server — tool registration & routing (stdio + SSE)
│   ├── connection.py          # COM connection manager (auto-connect, reconnect, shutdown)
│   ├── utils.py               # Shared validation utilities
│   └── tools/
│       ├── __init__.py
│       ├── document.py        # Document management (10 tools)
│       ├── sketcher.py        # 2D sketching (11 tools)
│       ├── part_design.py     # 3D part design (15 tools)
│       ├── assembly.py        # Assembly/product (9 tools)
│       ├── measurement.py     # Measurement & analysis (6 tools)
│       └── export.py          # Export & view control (4 tools)
├── tests/                     # pytest test suite (154 tests)
│   ├── conftest.py            # Shared COM mocking infrastructure
│   ├── test_*.py              # Module-specific tests
│   └── test_sse.py            # SSE transport tests
├── pyproject.toml
└── README.md
```

### Data flow

**Stdio mode** (Claude Desktop / Claude Code):

```
Claude (Desktop/Code)
    │
    │ stdio (MCP JSON-RPC)
    ▼
catia_mcp/server.py  (MCP Server)
    │
    │ Tool routing + asyncio lock (COM is single-threaded)
    ▼
catia_mcp/tools/*.py  (Tool modules)
    │
    │ win32com.client (COM Automation)
    ▼
CATIA V5 Application
```

**SSE mode** (LM Studio / vLLM.rs / remote LLM):

```
LM Studio (Browser)
    │
    ├── SSE HTTP ──→ catia_mcp --sse :8765 ──→ CATIA V5
    │
    └── OpenAI API ──→ vLLM (remote) :8010
```

## Complete Tool Reference

All dimensions are in **millimeters**, angles in **degrees**.

---

### 📄 Document Tools (10)

| Tool | Parameters | Required | Description |
|------|------------|----------|-------------|
| `catia_connect` | — | — | Connect to CATIA V5. Attaches to a running instance or launches a new one. Must be called before any other CATIA tool. |
| `catia_disconnect` | — | — | Disconnect from CATIA V5 (does not close CATIA). |
| `catia_close` | — | — | Gracefully close CATIA V5 entirely. Closes all open documents and quits. Does **not** save unsaved changes. |
| `catia_new_part` | `name` | — | Create a new empty Part document for single-body 3D modeling. |
| `catia_new_product` | `name` | — | Create a new empty Product (assembly) document. |
| `catia_open_document` | `file_path` | `file_path` | Open an existing `.CATPart`, `.CATProduct`, or `.CATDrawing`. |
| `catia_save_document` | `file_path` | — | Save the active document. Optional `file_path` for Save As. |
| `catia_close_document` | `save` | — | Close the active document. Optional `save` to prompt saving. |
| `catia_list_documents` | — | — | List all open documents with their types and paths. |
| `catia_get_active_document_info` | — | — | Get detailed info about the active document: name, type, path, part bodies, features, etc. |

---

### ✏️ Sketcher Tools (11)

| Tool | Parameters | Required | Description |
|------|------------|----------|-------------|
| `catia_create_sketch` | `plane` | — | Create a new 2D sketch on a reference plane: `xy` (front), `yz` (right), `zx` (top). Default: `xy`. |
| `catia_close_sketch` | — | — | Close the active sketch and return to Part Design. Must be called before creating 3D features. |
| `catia_sketch_line` | `x1`, `y1`, `x2`, `y2` | `x1`, `y1`, `x2`, `y2` | Draw a line from (x1, y1) to (x2, y2). Coordinates in mm. |
| `catia_sketch_rectangle` | `x1`, `y1`, `x2`, `y2` | `x1`, `y1`, `x2`, `y2` | Draw a rectangle defined by two opposite corners. Creates 4 lines. |
| `catia_sketch_centered_rectangle` | `cx`, `cy`, `width`, `height` | `width`, `height` | Draw a rectangle centered at (cx, cy). All values in mm. |
| `catia_sketch_circle` | `cx`, `cy`, `radius` | `radius` | Draw a circle. Center defaults to (0, 0) if not specified. |
| `catia_sketch_arc` | `cx`, `cy`, `radius`, `start_angle`, `end_angle` | `cx`, `cy`, `radius`, `start_angle`, `end_angle` | Draw a circular arc. Angles are counter-clockwise from positive X axis. |
| `catia_sketch_spline` | `points`, `closed` | `points` | Draw a spline through control points. `points` is a list of `[x, y]` in mm. |
| `catia_sketch_point` | `x`, `y` | `x`, `y` | Create a point in the active sketch. |
| `catia_sketch_constraint` | `type`, `value`, `geometry_index_1`, `geometry_index_2` | `type` | Add a dimensional/geometric constraint. Types: `distance`, `radius`, `angle`, `coincidence`, `tangent`, `perpendicular`, `parallel`, `horizontal`, `vertical`, `fix`. |
| `catia_sketch_get_geometry` | — | — | List all geometry elements in the active sketch with their indices and types. |

---

### 🔧 Part Design Tools (15)

| Tool | Parameters | Required | Description |
|------|------------|----------|-------------|
| `catia_pad` | `height`, `direction`, `symmetric`, `sketch_name` | `height` | Extrude a 2D profile into a 3D solid. `direction`: `normal` (default), `reverse`, `both`. |
| `catia_pocket` | `depth`, `direction`, `sketch_name` | `depth` | Cut extrusion — remove material by extruding a 2D profile inward. |
| `catia_shaft` | `angle`, `sketch_name` | — | Revolve a 2D profile around an axis. Default angle: 360° (full revolution). Sketch must contain a reference line. |
| `catia_groove` | `angle`, `sketch_name` | — | Revolution cut — remove material by revolving a 2D profile around an axis. |
| `catia_fillet` | `radius`, `edge_name` | `radius` | Add rounded edges. `edge_name` targets a specific edge; omit to fillet all. |
| `catia_chamfer` | `length`, `angle`, `edge_name` | `length` | Add beveled edges. Default angle: 45°. |
| `catia_hole` | `diameter`, `depth`, `type`, `threaded`, `sketch_name` | `diameter`, `depth` | Create a hole. `type`: `simple` (default), `counterbored`, `countersunk`. |
| `catia_rect_pattern` | `dir1_count`, `dir1_spacing`, `dir2_count`, `dir2_spacing`, `feature_name` | `dir1_count`, `dir1_spacing` | Duplicate a feature in a grid along two directions. |
| `catia_circ_pattern` | `count`, `angular_spacing`, `feature_name` | `count` | Duplicate a feature around a central axis. |
| `catia_mirror` | `plane`, `feature_name` | `plane` | Mirror a feature or body about a plane: `xy`, `yz`, or `zx`. |
| `catia_shell` | `thickness`, `faces_to_remove` | `thickness` | Hollow out a solid, leaving walls of specified thickness. Optionally remove faces for openings. |
| `catia_draft` | `angle`, `face_name`, `pulling_direction` | `angle` | Add draft angle for mold-release. Tapers faces relative to a pulling direction. |
| `catia_thickness` | `offset`, `face_name` | `offset` | Offset faces inward (negative) or outward (positive). |
| `catia_list_features` | — | — | List all features in the active Part Body with names and types. |
| `catia_list_edges` | — | — | List all edges of the active solid body for use with fillet/chamfer. |

---

### 📦 Assembly Tools (9)

| Tool | Parameters | Required | Description |
|------|------------|----------|-------------|
| `catia_add_component` | `file_path` | `file_path` | Add an existing `.CATPart` or `.CATProduct` as a component in the active assembly. |
| `catia_add_new_part` | `name` | — | Create a new empty Part directly inside the active assembly. |
| `catia_fix_constraint` | `component_name` | `component_name` | Fix a component in place (remove all degrees of freedom). |
| `catia_coincidence_constraint` | `component1`, `component2`, `element1`, `element2` | `component1`, `component2` | Align axes, planes, or points of two components. |
| `catia_offset_constraint` | `component1`, `component2`, `offset` | `component1`, `component2`, `offset` | Maintain a constant distance between two faces/planes. |
| `catia_angle_constraint` | `component1`, `component2`, `angle` | `component1`, `component2`, `angle` | Set an angle between two axes or planes. |
| `catia_move_component` | `component_name`, `tx`, `ty`, `tz`, `rx`, `ry`, `rz` | `component_name` | Move a component by translation (mm) and/or rotation (degrees). |
| `catia_list_components` | — | — | List all assembly components with names and positions. |
| `catia_list_constraints` | — | — | List all assembly constraints in the active product. |

---

### 📏 Measurement Tools (6)

| Tool | Parameters | Required | Description |
|------|------------|----------|-------------|
| `catia_measure_distance` | `element1`, `element2` | `element1`, `element2` | Measure the minimum distance between two geometry elements. Returns distance in mm. |
| `catia_get_inertia` | `density` | — | Get inertia properties: volume, surface area, center of gravity, mass (if density given), moments of inertia. |
| `catia_get_bounding_box` | — | — | Get the bounding box of the active part. Returns min/max coordinates in mm. |
| `catia_get_parameters` | `filter` | — | List all user-defined and computed parameters. Optional `filter` for partial name matching. |
| `catia_set_parameter` | `name`, `value` | `name`, `value` | Set the value of a named parameter. Useful for parametric design. |
| `catia_update_part` | — | — | Force update/rebuild of the active part. Recalculates all features. |

---

### 📤 Export & View Tools (4)

| Tool | Parameters | Required | Description |
|------|------------|----------|-------------|
| `catia_export` | `file_path`, `format` | `file_path` | Export to: STEP (`.stp`), IGES (`.igs`), STL (`.stl`), 3DXML (`.3dxml`), VRML (`.wrl`), PDF, CGR. Format is auto-detected from file extension. |
| `catia_screenshot` | `file_path`, `width`, `height` | `file_path` | Capture the current 3D view as PNG, JPG, or BMP. Default: 1920×1080. |
| `catia_set_view` | `view` | `view` | Set view orientation: `front`, `back`, `top`, `bottom`, `left`, `right`, `isometric`. |
| `catia_fit_all` | — | — | Fit all geometry in the current 3D view (zoom to fit). |

---

## Testing

This project includes a comprehensive pytest test suite (154 tests) with mocked COM, so tests run on any OS without CATIA installed:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Troubleshooting

### "pywin32 is not installed"

```bash
pip install pywin32
```

This server requires **Windows**. It will not work on macOS or native Linux.

### "Failed to connect to CATIA V5"

1. Make sure CATIA V5 is running
2. Register CATIA as COM server: run `cnext.exe /regserver` from `C:\Program Files\Dassault Systemes\B<version>\code\bin\`
3. Ensure no modal dialog is blocking CATIA

### "No active document"

Create or open a document first using `catia_new_part`, `catia_new_product`, or `catia_open_document`.

### COM ByRef array limitations

Some measurement methods (`get_inertia`, `get_bounding_box`) use ByRef arrays. The server includes fallback strategies (early binding → late binding → property access). If issues persist, try `pycatia` as an alternative backend.

### SSE connection fails

1. Make sure the SSE server is running: `python -m catia_mcp --sse`
2. Check Windows Firewall — port 8765 must be allowed for inbound TCP
3. Verify you activated the virtual environment before starting the server
4. Confirm LM Studio (or your MCP client) is pointing to the correct URL: `http://localhost:8765/sse` or `http://<windows-ip>:8765/sse` for remote access
5. Check the log file at `%TEMP%\catia-mcp\catia_mcp.log` for connection errors

### Server not starting

Check the log file at `%TEMP%\catia-mcp\catia_mcp.log` (Windows) or `$TEMP/catia-mcp/catia_mcp.log` for detailed error output.

## Robustness Features

- **Auto-connect**: The server automatically connects to CATIA on first tool use (except for `catia_connect`/`disconnect`/`close`)
- **Auto-reconnect**: If the COM connection drops, the server attempts to reconnect transparently
- **Thread safety**: All COM calls are serialized via `asyncio.Lock` (CATIA COM is single-threaded)
- **Path normalization**: File paths with forward slashes are automatically converted to backslashes for CATIA
- **Graceful shutdown**: `catia_close` closes all documents and quits CATIA cleanly
- **Input validation**: All tool inputs are validated before COM calls to provide clear error messages

## Contributing

This project is open-source. Contributions welcome:

- **Wireframe & Surface (GSD)** tools
- **Drawing** tools (2D drafting)
- **Knowledgeware** (formulas, rules, check)
- **pycatia backend** as alternative to raw win32com
- **3DEXPERIENCE** CATIA support
- **Windows integration tests** with real CATIA

Please open an issue or pull request on [GitHub](https://github.com/Zippo2000/catia-v5-mcp-server).

## License

MIT — see [LICENSE](LICENSE) for details.

## Credits

Inspired by:
- [SolidWorks-MCP](https://github.com/Sam-Of-The-Arth/SolidWorks-MCP)
- [freecad-mcp](https://github.com/contextform/freecad-mcp)
- [abaqus-mcp-server](https://github.com/jianzhichun/abaqus-mcp-server)
- [pycatia](https://github.com/evereux/pycatia)