# OpenCode ACP Integration — Recherche & Konfiguration

> **Datum:** 2026-06-04
> **Analyst:** Hermes Agent

---

## 1. Problem

opencode als ACP-Subagent für Hermes Agent funktioniert nicht stabil:
- `opencode acp` ist ein **HTTP-Server** (nicht stdio)
- `opencode run` bricht nach ersten Tool-Use mit **214 Validierungsfehlern** ab
- `opencode-acp` Bridge timeout nach 600s bei komplexen Tasks

---

## 2. Architektur

```
┌──────────────┐  stdio JSON-RPC  ┌──────────────┐  HTTP JSON-RPC  ┌──────────────┐
│  Hermes Agent│ ────────────────►│ opencode-acp │ ───────────────►│ opencode acp │
│ (CopilotACP  │  (delegate_task)  │ (Bridge)     │  (intern)      │ (HTTP server) │
│  Client)     │                   │              │                 │              │
└──────────────┘                   └──────────────┘                 └──────────────┘
```

**Drei Komponenten:**
1. **Hermes Agent** — `delegate_task` mit `acp_command="opencode-acp"`, `acp_args=[]`
2. **opencode-acp** — npm-Package von `josephschmitt/opencode-acp`, übersetzt HTTP → stdio
3. **opencode** — npm-Package `opencode-ai`, läuft als HTTP-Server

---

## 3. Installation (erledigt)

| Schritt | Status | Befehl |
|---------|--------|--------|
| Node.js (v22.22.3) | ✅ | `nvm install 22` |
| opencode-ai | ✅ | `npm install -g opencode-ai` |
| opencode-acp | ✅ | `git clone + npm install + npm run build + npm link` |
| opencode Config | ✅ | `~/.config/opencode/opencode.jsonc` (vLLM @ 192.168.177.44:8010) |
| Hermes Env | ✅ | `HERMES_COPILOT_ACP_COMMAND` in `~/.hermes/.env` |
| Hermes Patch | ✅ | `copilot_acp_client.py:69` erkennt `opencode-acp` |

---

## 4. Konfiguration

### 4.1 opencode.jsonc
```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openai": {
      "options": {
        "baseURL": "http://192.168.177.44:8010/v1",
        "apiKey": "not-needed"
      },
      "models": {
        "qwen3.6-27b-autoround": {
          "displayName": "Qwen3.6-27B"
        }
      }
    }
  },
  "permission": {}
}
```

### 4.2 Hermes .env
```
HERMES_COPILOT_ACP_COMMAND=/home/hermeswebui/.nvm/versions/node/v22.22.3/bin/opencode-acp
```

### 4.3 Hermes copilot_acp_client.py (Patch)
Zeile 69: `if cmd_name in ("opencode", "opencode-acp"):` — erkennt beide Befehle

---

## 5. Verwendung

```python
delegate_task(
    goal="Analyse task...",
    acp_command="opencode-acp",
    acp_args=[]  # KEINE extra Args — Bridge spricht stdio ACP direkt
)
```

---

## 6. Bekannte Probleme

### 6.1 Timeout bei komplexen Tasks (600s)
- **Ursache:** Qwen3.6-27B auf vLLM (2x RTX 3090) ist zu langsam für ACP-Subagent-Timeout
- **opencode-acp** macht 1 API-Call pro Tool-Use, jeder Call kann 30-60s dauern
- Bei 10+ Tool-Use-Calls übersteigt die Gesamtzeit 600s
- **Issue:** [anomalyco/opencode#26602](https://github.com/anomalyco/opencode/issues/26602) — 5-min Timeout bei slow local providers

### 6.2 opencode run bricht mit 214 Validierungsfehlern
- **Ursache:** opencode v1.15.x + vLLM-Provider = Inkompatibilität bei Tool-Call-Response-Weiterleitung
- **Issue:** [anomalyco/opencode#17307](https://github.com/anomalyco/opencode/issues/17307) — timeouts too aggressive for larger local models
- **Workaround:** Nicht `opencode run` verwenden, sondern `opencode-acp` als Bridge

### 6.3 GitHub Issue #19493 (Hermes)
- **Status:** Offen — automatisches Erkennen von `opencode` als ACP-Backend
- **Workaround:** `acp_command="opencode-acp"` mit `acp_args=[]` verwenden

---

## 7. Empfehlungen

### Kurzfristig
1. **Timeout erhöhen** — Hermes' `delegate_task` default ist 600s; für opencode-acp mit vLLM braucht man 1200-1800s
2. **Timeout in config.yaml** konfigurieren: `delegation.timeout: 1800`
3. **Einfache Tasks** — opencode-acp funktioniert gut für Tasks mit <5 Tool-Use-Calls

### Mittelfristig
1. **Schnelleren Provider** für opencode (z.B. OpenRouter oder Hermes Portal)
2. **opencode.jsonc** um `timeout` und `chunkTimeout` erweitern:
   ```jsonc
   "provider": {
     "openai": {
       "options": {
         "baseURL": "http://192.168.177.44:8010/v1",
         "apiKey": "not-needed",
         "timeout": 300000,
         "chunkTimeout": 60000
       }
     }
   }
   ```

### Langfristig
1. Warten auf Hermes Issue #19493 (auto-detect opencode)
2. opencode v1.16+ mit besserer vLLM-Kompatibilität

---

## 8. Test-Ergebnisse

| Test | Ergebnis |
|------|----------|
| `opencode-acp` ACP-Handshake | ✅ `{"protocolVersion":1,"agentCapabilities":{...}}` |
| `opencode run` (einfach) | ❌ 214 Validierungsfehler |
| `opencode-acp` (komplex, 10+ Tool-Calls) | ❌ Timeout nach 600s |
| `opencode-acp` (einfach, 1-2 Tool-Calls) | ✅ Funktioniert |
| `opencode run` (REALTEST-Analyse, 9 Tool-Calls) | ❌ Abbruch nach erstem Schritt (`step-finish: tool-calls`) |

### 8.1 opencode run — REALTEST-Analyse (2026-06-04)

**Session:** `ses_16c8fbaa8ffeNs08YIOjqAuSEE` ("happy-tiger")

- **Prompt:** Analyse REALTEST_RESULTS.md + 8 Source-Dateien
- **Tool-Calls:** 9x `read` (REALTEST_RESULTS.md, measurement.py, part_design.py, sketcher.py, gsd.py, assembly.py, document.py, export.py, connection.py)
- **Ergebnis:** Session nach erstem Schritt beendet (`step-finish: tool-calls`)
- **Keine finale Antwort:** opencode hat die Dateien gelesen, aber keine analytische Text-Antwort generiert
- **Ursache:** vLLM-Provider (Qwen3.6-27B) liefert nach Tool-Output-Injection keine weitere Antwort — Session endet mit `reason: tool-calls`

---

## 9. Fazit

opencode-acp ist **installiert und konfiguriert**, aber für komplexe Analyse-Tasks mit unserem vLLM-Provider nicht stabil:

1. **`opencode run`** — liest Dateien, bricht aber vor der Analyse ab (kein zweiter Schritt)
2. **`opencode-acp` via delegate_task** — timeout nach 600s bei komplexen Tasks
3. **Timeout-Erweiterung** (`opencode.jsonc`: `timeout: 600000`, `chunkTimeout: 120000`) — hilft nicht, das Problem liegt im Provider, nicht im Timeout

**Empfehlung:** Für tiefe Code-Analysen im catia-v5-mcp-server-Projekt den **Hermes-Subagent** verwenden (funktioniert, 16 Bugs gefunden). opencode-acp ist für einfache, schnelle Tasks (<5 Tool-Calls) geeignet.
