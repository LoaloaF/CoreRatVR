# Plan: CoreRatVR Architecture & Workflow — `ARCHITECTURE.md`

Write a `ARCHITECTURE.md` at the repo root (`/Users/loaloa/homedataAir/phd/ratvr/VirtualReality/CoreRatVR/ARCHITECTURE.md`) covering the following sections in order.

---

## Section 1 — Overview paragraph

FastAPI server on `:8000`, Svelte UI at `/ui`, orchestrates hardware I/O via shared memory on Linux/macOS; designed for rodent VR neuroscience experiments. One sentence per major concern (hardware bridging, memory bus, logging, post-processing).

---

## Section 2 — Component Map

Five components, prose + short bullet lists:

- **API server** (`main_vr.py`) — `app.state.state` as single source of truth; keys `procs` (PID dict), `shm` (created flags), `initiated`, `paradigmRunning`, SHM interface handles.
- **Config singleton** (`Parameters.py`) — all directories, SHM names/sizes, camera specs, hardware details; distinguish locked keys (all `SHM_NAME_*`, System/Hardware group) vs. patchable keys editable at runtime via `PATCH /parameters/{key}`.
- **SHM bus** (`SHM/`) — three region types, JSON descriptor files written to `SHM_STRUCTURE_DIRECTORY/`, macOS file-backed shim (`OSXFileBasedSHM`).
- **Subprocess pool** (`process_launcher.py`) — all `read2SHM/`, `dataloggers/`, Unity binary, Maxwell binaries; each launched via `subprocess.Popen` with its log file; CLI args pass JSON descriptor paths so subprocesses find SHM by path.
- **Session data store** — HDF5 per modality in a timestamped session directory under `DATA_DIRECTORY/`.

---

## Section 3 — ASCII Architecture Diagram

Include a diagram showing:

```
Browser UI (Svelte /ui)
        │ HTTP / WebSocket  :8000
        ▼
main_vr.py  (FastAPI / uvicorn)
app.state.state
  ├─ procs  {name → PID}
  ├─ shm    {name → bool}
  ├─ initiated / paradigmRunning
  └─ SHM interface handles
        │
  ┌─────┴───────────────────────────────────┐
  │ POST /shm/create_*   POST /procs/launch_* │
  │                                           │
  ▼                                           ▼
shm_creation.py                     process_launcher.py
creates SHM regions                 subprocess.Popen(...)
+ JSON descriptors                  → read2SHM/*
                                    → dataloggers/*
                                    → Unity / Maxwell binaries
        │                                     │
        └──────── SHARED MEMORY BUS ──────────┘
          termflag  paradigmflag  ballvelocity
          portentaoutput  portentainput
          unityoutput  unityinput
          facecam  ttlcam2/3/4  bodycam  unitycam
        │
        ▼
HDF5 session files (written by loggers during paradigm)
  portenta_output.hdf5
  unity_output.hdf5
  {cam_name}.hdf5  (per camera)
        │
        ▼
session_processing/process_session.py  →  NAS  +  DB
```

Callout boxes: `paradigmflag` = start/stop gate for all loggers; `termflag` = shutdown broadcast to all subprocesses.

---

## Section 4 — SHM Region Types (medium depth)

Explain the **three region types** in prose:

1. **`singlebyte` flag** — 1-byte region; `FlagSHMInterface` wraps it with `set()`, `reset()`, `is_set()`. Used as broadcast signals readable by every process without coordination.
2. **`cyclic_packages` ring-buffer** — `[pkg_0][pkg_1]…[pkg_N-1][write_ptr (8 B)]`; `CyclicPackagesSHMInterface` provides `push()` / `popitem()`. Lock-free single-writer, single-reader design; write pointer stored at tail so any reader can find it.
3. **`cyclic_frames` ring-buffer** — same structure as `cyclic_packages` but each slot is `[80 B metadata header][raw frame bytes]`; used for camera streams.

Then a **representative table** (~5 key regions):

| SHM name | Type | Key size | Producer | Consumers | Purpose |
|---|---|---|---|---|---|
| `termflag` | singlebyte | 1 B | API server | all subprocesses | Shutdown broadcast |
| `paradigmflag` | singlebyte | 1 B | API server | all loggers, portenta bridge | Start/stop logging gate |
| `ballvelocity` | cyclic_packages | 4096 × 80 B | `portenta2shm2portenta` | `log_portenta`, streamer | Treadmill velocity stream |
| `unityoutput` | cyclic_packages | 128 × 256 B | Unity binary | `log_unity`, WS streamer | VR frame + trial events |
| `facecam` | cyclic_frames | 32 × (80 B + frame) | `vimbacam2shm` | `log_camera_cyclic`, WS streamer | Face camera frames |

Note: descriptor JSON for each region is written to `SHM_STRUCTURE_DIRECTORY/` and passed to subprocesses via CLI argument `--xxx_shm_struc_fname`.

---

## Section 5 — Session Lifecycle / Enforced Workflow

Numbered sequence keyed to real API endpoints. Call out that `validate_state()` in `backend_helpers.py` enforces order and raises HTTP 400 for out-of-sequence calls.

1. `POST /initiate` — creates timestamped session directory (`DATA_DIRECTORY/{ts}_{animal}_{paradigm}/`), writes `parameters.json`, starts `CustomLogger`. **Must happen before any SHM or process endpoints.**
2. Set session metadata (can be done in any order after initiate):
   - `POST /session/paradigm/{name}`
   - `POST /session/animal/{name}`
   - `POST /session/animalweight/{value}`
3. `POST /shm/create_*` — create each required SHM region. The server holds writer handles to `termflag`, `paradigmflag`, and `unityinput` directly.
4. `POST /procs/launch_*` — start each subprocess. All subprocesses are now running but **paused** — they loop on `paradigmflag.is_set()` returning `False`.
5. `POST /start_paradigm` — calls `SessionParamters.handle_start_session()`, then **raises `paradigmflag`** → all loggers unblock simultaneously and begin writing HDF5.
6. `POST /stop_paradigm` — calls `SessionParamters.handle_stop_session()`, then **lowers `paradigmflag`** → loggers pause but stay alive (ready for another start/stop cycle).
7. `POST /raise_term_flag` — **raises `termflag`** → all subprocesses exit their loops → SHM regions are deleted → optionally launches `session_processing/process_session.py` → server state fully reset.

---

## Section 6 — `start_paradigm` / `stop_paradigm` Mechanics

Detail what happens at each gate transition:

**`POST /start_paradigm` triggers:**
- `SessionParamters.handle_start_session()`:
  - Records `start_time = datetime.now()`
  - Parses `paradigm_id` from paradigm filename (chars 1–4, e.g. `P0800_…` → `800`)
  - Copies paradigm `.xlsx` to session directory
  - Reads Excel sheets: `Environment`, `EnvParameters`, `SessionParameters`
  - Loads FSM JSON assets: `fsm_states.json`, `fsm_transitions.json`, `fsm_decisions.json`, `fsm_actions.json` from `UnityRatVR/paradigmFSMs/`
- `paradigm_running_shm_interface.set()` — **raises `paradigmflag`**
- All loggers (`log_portenta`, `log_unity`, `log_camera_cyclic` × N, `log_ephys`) unblock from their wait loop and call `shm.reset_reader()` to skip stale data, then start writing HDF5

**`POST /stop_paradigm` triggers:**
- `SessionParamters.handle_stop_session()`:
  - Records `stop_time`, computes `duration`
  - Writes `session_parameters.json` to session directory (merged metadata + FSM assets)
- `paradigm_running_shm_interface.reset()` — **lowers `paradigmflag`**
- All loggers return to their wait loop (no process restart required)

**Arduino Portenta side-effect (`portenta2shm2portenta.py`):**
- The serial bridge polls `paradigmflag` on every loop iteration
- On **rising edge** (low → high): sends `W1000\r\n` to the serial port (1000 ms pause command)
- On **falling edge** (high → low): sends `W2000\r\n` to the serial port (2000 ms pause command)
- This synchronises the Arduino's internal state machine to the paradigm gate

---

## Section 7 — Session Directory Contents

Table of files written per session:

| File | Written by | Contents |
|---|---|---|
| `parameters.json` | `POST /initiate` | Full `Parameters` singleton snapshot |
| `session_parameters.json` | `POST /stop_paradigm` | Animal, paradigm metadata, FSM JSON assets, timing |
| `unity_output.hdf5` | `log_unity` | Keys: `unityframes` (VR frame packages), `trialPackages` (trial events) |
| `portenta_output.hdf5` | `log_portenta` | Keys: `ballvelocity` (treadmill), `portentaoutput` (events) |
| `facecam.hdf5` | `log_camera_cyclic` | JPEG-encoded frames + frame IDs; separate `*_packages.hdf5` for metadata |
| `ttlcam2/3/4.hdf5` | `log_camera_cyclic` | Same as face cam |
| `bodycam.hdf5` | `log_camera_cyclic` | Same as face cam (color: 3-channel) |
| `unitycam.hdf5` | `log_camera` (single-frame variant) | JPEG frames from Unity render camera |
| Ephys files | mxwserver binary (Maxwell) | Raw MEA1K recordings; path set by `log_ephys` via `mx.Saving` API |
| `*.log` × N | `CustomLogger` per subprocess | Per-process log files in `LOGGING_DIRECTORY/` |

---

## Section 8 — GUI / Operator Experience

*This section is inferred from endpoint structure and the Svelte UI mount at `/ui`. Label it clearly as inferred.*

The operator interacts entirely through the browser UI (`http://localhost:8000/ui`). The UI is a Svelte single-page app served from `UIRatVR/dist/`. UI state is driven by an SSE stream (`GET /statestream`, polling every 100 ms) which reflects `app.state.state` live.

**Operator flow:**

1. **Start the server**: run `python main_vr.py` in the terminal; navigate to `http://localhost:8000/ui`.
2. **Configure parameters**: edit mutable fields (animal names, paradigm directories, camera IDs, etc.) via the Parameters panel → `PATCH /parameters/{key}`. Locked fields (hardware/SHM names) are read-only.
3. **Initiate a session**: click "Initiate" button → `POST /initiate`. Session directory is created; logger starts. The UI transitions to the session setup view.
4. **Select animal and paradigm**: dropdown populated from `GET /animals` and `GET /paradigms` → `POST /session/animal/{name}`, `POST /session/paradigm/{name}`, `POST /session/animalweight/{val}`.
5. **Create SHM regions**: click per-region "Create" buttons (or a global "Create All") → `POST /shm/create_*`. Indicators in the UI turn green as each region is confirmed created.
6. **Launch processes**: click per-process "Launch" buttons (or "Launch All") → `POST /procs/launch_*`. Process status indicators show PID or ✗. Live camera previews become available via WebSocket streams (`/stream/facecam`, `/stream/bodycam`, etc.).
7. **Start paradigm**: click "Start" → `POST /start_paradigm`. A timer starts in the UI. Live data streams (`/stream/ballvelocity`, `/stream/unityoutput`) become active. All loggers begin recording.
8. **Monitor**: live velocity plot, camera feeds, and Unity output are rendered via WebSocket. Log file panel (`/stream/logfiles`) shows rolling subprocess logs.
9. **Stop paradigm**: click "Stop" → `POST /stop_paradigm`. Timer freezes. Loggers pause. Data is flushed to HDF5.
10. **Terminate session**: click "Terminate" → `POST /raise_term_flag` with options (trash session / copy to NAS / launch processing). All processes exit; SHM cleaned up; UI resets to initial state.

**Inspect mode** (no hardware required):
- Navigate to the Inspect panel → `POST /inspect/initiate_session_selection/{session_name}` (sessions listed from NAS via `GET /inspect/sessions`).
- Browse trial data (`GET /inspect/trials`), events (`GET /inspect/events`), frames (`GET /inspect/unityframes`).
- WebSocket streams support `?inspect=true` to replay camera frames and package data from NAS HDF5 at arbitrary timestamps.
- Exit with `POST /inspect/terminate_inspection`.

---

## Writing Guidelines

- Audience: new lab member who knows Python but is new to this codebase.
- Prose tone: technical, precise, no filler sentences.
- All file references should link to actual files in the repo.
- All API endpoint paths should be formatted as inline code.
- No frontmatter in the output file.
- No code blocks in the final `ARCHITECTURE.md` prose sections — use tables, markdown lists, and the ASCII diagram only.
- The ASCII diagram should be inside a fenced code block.
