# PathSim to PathView PVM Converter

## Overview

The `py_to_pvm.py` converter transforms PathSim Python model scripts (`.py`) into PathView-compatible `.pvm` JSON files that can be uploaded and streamed on the PathView server.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | Server runs 3.11; local can be 3.12 |
| PathSim | 0.20.0+ | Must be importable or use `--pathsim-root` |
| NumPy | any | Required by PathSim |

### Install PathSim

```bash
pip install pathsim
```

Or point to a local clone:

```bash
git clone https://github.com/your-org/pathsim.git pathsim-master
```

---

## Quick Start

### Single file conversion

```bash
python py_to_pvm.py example_cascade.py -o example_cascade.pvm
```

### With local PathSim source

```bash
python py_to_pvm.py example_cascade.py --pathsim-root ./pathsim-master
```

### Batch conversion (all examples in a directory)

```bash
python py_to_pvm.py examples --batch --pathsim-root ./pathsim-master
```

### Batch with subdirectories, skipping broken imports

```bash
python py_to_pvm.py examples --batch --recursive --skip-missing-deps --quiet
```

---

## CLI Reference

```
python py_to_pvm.py <input> [options]
```

| Argument | Description |
|---|---|
| `input` | Path to a `.py` file or a directory (with `--batch`) |
| `-o, --output` | Output `.pvm` path (single file) or directory (batch) |
| `--sim-var` | Name of the `Simulation` variable in the script (auto-detected if omitted) |
| `--name` | Model name for PVM metadata |
| `--pathsim-root` | Path to local PathSim repo root (adds `src/` to `sys.path`) |
| `--code-context` | `auto` (default), `full`, or `none` — controls codeContext generation |
| `--duration` | Override simulation duration (Python expression as string) |
| `--batch` | Convert all `.py` files in the input directory |
| `--recursive` | Recursively search subdirectories in batch mode |
| `--skip-missing-deps` | Skip files that fail due to missing optional imports |
| `--quiet` | Suppress progress output and model script stdout |

---

## How the Converter Works

The converter follows this pipeline:

### Step 1 — Execute the Python script

The input `.py` file is executed as a module via `importlib`. This runs the script and populates `module.__dict__` with all variables, including the `Simulation` object, blocks, connections, and events.

### Step 2 — Locate the Simulation object

The converter scans module globals for an instance of `pathsim.simulation.Simulation`. If multiple exist, use `--sim-var` to specify which one. It extracts:

- **Blocks** — all simulation blocks (`Source`, `Integrator`, `Gain`, `Scope`, custom `Block` subclasses, etc.)
- **Connections** — wiring between block ports
- **Events** — `Schedule`, `ZeroCrossing`, `Condition` events
- **Solver settings** — `dt`, `Solver`, adaptive tolerances

### Step 3 — AST-based parameter extraction

Instead of relying on `inspect` or `repr()`, the converter parses the original Python source with `ast` to extract constructor keyword arguments as literal expressions. This preserves symbolic expressions like `lambda t: np.sin(omega*t)` exactly as written.

### Step 4 — Build the PVM graph

Each block becomes a **node** with:
- A unique `id` derived from the variable name
- `type` matching the PathSim class name
- `params` dict with constructor arguments
- `position` for layout

Each connection becomes an **edge** with `sourceNodeId`, `sourcePort`, `targetNodeId`, `targetPort`.

**Subsystem** nodes get a recursive `graph` sub-structure containing their internal blocks and connections.

### Step 5 — Normalize connections for streaming

PathView's streaming engine expects scalar signals on each port. The converter inserts adapter blocks when needed:

- **`normalize_vector_scope_connections`** — Splits vector inputs to `Scope` into individual scalar channels via `Demux` + `Function` adapters
- **`normalize_stream_target_scalar_inputs`** — Adds scalar extraction for blocks receiving vector signals
- **`normalize_source_like_scalar_outputs`** — Wraps `Source`-like blocks that output vectors

### Step 6 — Generate Code Context

The `codeContext.code` field contains Python code that the server executes before building the simulation. In `auto` mode, the converter uses AST analysis to include only:

- Import statements
- Class definitions (custom `Block` subclasses, helper classes)
- Global variable assignments (constants like `omega = 2 * np.pi * 1e3`)
- Function definitions

It **excludes** block instantiations, connection wiring, and simulation setup (those are reconstructed from the graph).

### Step 7 — Inject monkey patches

A **monkey patch** is a technique where you modify or extend existing classes/functions **at runtime**, without changing their original source code. This is needed because the PathView server runs a different PathSim version than local, and we cannot modify either the server's library or its frontend code.

Two monkey patches are prepended to `codeContext.code`:

1. **Register patch** — Fixes `ValueError: setting an array element with a sequence` when PathView's streaming engine writes scalar values into `Register` objects
2. **Block.__call__ patch** — Redirects `block(t)` calls to `block.update(t)` because the server's PathSim version calls `block(t)` while `Block.__call__` only accepts `self`

#### Register patch example

The PathView streaming engine passes a 1-element list like `[3.14]` where `Register` expects a plain `float`. The patch intercepts `Register.__setitem__` and unwraps it:

```python
# Before patch: Register[key] = [3.14]  → crashes with ValueError
# After patch:  Register[key] = 3.14    → works fine

_orig_setitem = Register.__setitem__
def _pv_safe_setitem(self, key, value):
    if isinstance(value, (list, tuple)) and len(value) == 1:
        value = value[0]       # unwrap [3.14] → 3.14
    _orig_setitem(self, key, value)
Register.__setitem__ = _pv_safe_setitem   # ← this is the monkey patch
```

#### Block.__call__ patch example

The server calls `block(t)` but `Block.__call__` only accepts `self`. The patch redirects to `block.update(t)`:

```python
_orig_block_call = Block.__call__
def _pv_safe_block_call(self, *args, **kwargs):
    if args or kwargs:
        return self.update(*args, **kwargs)  # redirect block(t) → block.update(t)
    return _orig_block_call(self)
Block.__call__ = _pv_safe_block_call   # ← monkey patch
```

Each patch checks a guard flag (e.g., `hasattr(Register, '_pv_patched')`) to avoid double-patching if the code runs more than once. The patches are scoped to the current execution context and do not persist beyond the simulation session.

### Step 8 — Write the PVM JSON

The final `.pvm` file is a JSON document with this structure:

```json
{
  "version": "1.0.0",
  "metadata": { "created": "...", "modified": "...", "name": "..." },
  "graph": {
    "nodes": [ ... ],
    "connections": [ ... ],
    "annotations": []
  },
  "events": [ ... ],
  "codeContext": { "code": "..." },
  "simulationSettings": {
    "duration": "...", "dt": "...", "solver": "...",
    "adaptive": false, "atol": "...", "rtol": "...", "ftol": "...",
    "dt_min": "", "dt_max": ""
  }
}
```

---

## Known Pitfalls and Solutions

### 1. Lambda trailing parenthesis

**Problem:** `callable_to_expr()` extracts lambda bodies using regex, which can capture trailing `)` from enclosing calls:

```python
Source(lambda t: np.sin(omega*t))  # Extracted as: lambda t: np.sin(omega*t))  ← extra )
```

**Solution:** The converter now progressively strips trailing `)` and `,` characters and validates with `ast.parse(expr, mode="eval")` until the expression is syntactically valid.

### 2. Missing imports for custom Block subclasses

**Problem:** When a script defines a custom class like `class SAR(Block):`, the `codeContext` must include `from pathsim.blocks._block import Block`. Earlier versions filtered this import out.

**Solution:** Rebuild the PVM with the current converter. The AST-based code context extractor now preserves all imports needed by class definitions. If you encounter `NameError: name 'Block' is not defined`, regenerate the PVM.

### 3. Missing Schedule import

**Problem:** Scripts using `Schedule` events need `from pathsim.simulation import Schedule` in the `codeContext`. The server cannot find the `Schedule` class otherwise.

**Solution:** The converter detects event subclasses and injects the required imports automatically.

### 4. Subsystem graph structure

**Problem:** PathView expects `Subsystem` nodes to have a nested `graph` field containing their internal blocks and connections. Without it, the viewer crashes.

**Solution:** `build_subsystem_graph()` recursively builds the internal graph for each `Subsystem` node, including filtering out auto-created events (bound closures that cannot be serialized).

### 5. Unreferrable closure in Schedule events

**Problem:** When a `Schedule` event uses a lambda `func_act` that captures local variables (a closure), it cannot be serialized into the PVM JSON. The server gets `NameError: name '_set' is not defined`.

**Solution:** The converter filters out events where `func_act` is a bound closure (auto-created internal events). Only user-defined events with serializable function references are included.

### 6. Block.__call__() argument mismatch

**Problem:** The PathView server's PathSim version calls `block(t)` during streaming, but `Block.__call__(self)` only accepts `self` — no positional arguments. This causes: `Block.__call__() takes 1 positional argument but 2 were given`.

**Solution:** A monkey patch in `codeContext` redirects `block(t)` to `block.update(t)`:

```python
def _pv_safe_block_call(self, *args, **kwargs):
    if args or kwargs:
        return self.update(*args, **kwargs)
    return _orig_block_call(self)
```

### 7. Register scalar assignment crash

**Problem:** PathView's streaming engine sometimes passes a 1-element list or array where a scalar float is expected, causing `ValueError: setting an array element with a sequence`.

**Solution:** A monkey patch on `Register.__setitem__` and `Register.update_from_array` unwraps single-element containers to plain floats before assignment.

### 8. Parameter quoting mismatch

**Problem:** PathView's frontend JavaScript generates simulation code using `${key}=${value}` (no quotes). If the converter or test harness wraps values in `repr()`, strings get extra quotes causing `SyntaxError`.

**Solution:** Use raw values, not `repr()`, when interpolating parameters into generated code. The frontend's `c5()` function uses direct value interpolation.

### 9. Vector-to-scalar normalization

**Problem:** PathView streams scalar values per port. If a `Source` outputs a vector (e.g., `np.array([1, 2, 3])`) or a `Scope` receives a vector input, the streaming engine crashes.

**Solution:** The converter inserts `Demux` and `Function(lambda x: _pv_scalar(x, idx))` adapter blocks to split vector signals into individual scalar channels. The `_pv_scalar()` helper is injected into `codeContext`.

### 10. Server connection errors (net::ERR_CONNECTION_CLOSED)

**Problem:** After uploading a PVM, streaming may fail with `net::ERR_CONNECTION_CLOSED`. This is a network/server issue, not a PVM issue.

**Solution:**
- Wait 1-2 minutes and retry (server may have restarted)
- Try a shorter simulation duration
- Try from a different network or use a VPN
- Check if the homepage loads; if not, the server is down
- Clear browser cache or try incognito mode

---

## Security Considerations

### Code execution via exec()

The converter **executes** the input Python script using `importlib` to introspect the `Simulation` object. This means:

- **Never convert untrusted `.py` files.** A malicious script can execute arbitrary code on your machine during conversion.
- Only convert scripts you have written or reviewed yourself.
- Run the converter in a sandboxed environment (container, VM) if processing third-party files.

### codeContext injection

The `codeContext.code` field in the PVM JSON is executed by the PathView server's Python worker. This means:

- **A tampered PVM file can execute arbitrary Python on the server.** Only upload PVMs you generated yourself.
- Do not share PVM files from untrusted sources.
- The server should ideally sandbox the worker process (container isolation, resource limits, no network access from worker).

### PVM file trust model

PVM files are **not safe to accept from untrusted parties**. They contain executable Python code in the `codeContext` field. Treat them like `.py` files — review before executing.

### Monkey patches

The converter injects monkey patches that modify core PathSim classes (`Register`, `Block`) at runtime. These patches:

- Are scoped to the current execution context
- Do not persist beyond the simulation session
- Are necessary to bridge version differences between local PathSim and the server's version
- Should be audited if you modify `py_to_pvm.py` to ensure they don't introduce vulnerabilities

### Recommendations

1. **Validate inputs** — Only convert `.py` files from trusted sources
2. **Review PVMs before upload** — Inspect `codeContext.code` for unexpected content
3. **Sandbox the server worker** — Run simulation workers in isolated containers with no outbound network
4. **Limit simulation resources** — Set maximum duration, step count, and memory limits server-side
5. **Use HTTPS** — Ensure PVM uploads and streaming connections use TLS
6. **Access control** — Restrict who can upload PVMs to the server

---

## Example PVM Files

This directory contains the following pre-built PVM files:

| PVM File | Description | Server Tested |
|---|---|---|
| `example_cascade.pvm` | Basic cascade of blocks | Yes (3224 steps) |
| `example_derivative.pvm` | Derivative block with streaming | Yes (121 steps) |
| `example_sar.pvm` | SAR ADC with custom Block subclass | Yes (737 steps) |
| `example_abs_braking.pvm` | ABS braking system | — |
| `example_adc.pvm` | ADC converter | — |
| `example_algebraicchain.pvm` | Algebraic chain | — |
| `example_algebraicloop.pvm` | Algebraic loop | — |
| `example_dcmotor.pvm` | DC motor model | — |
| `example_deltasigma.pvm` | Delta-sigma modulator | — |
| `example_diode.pvm` | Diode circuit | — |
| `example_dualslope.pvm` | Dual-slope ADC | — |
| `example_elastic_pendulum.pvm` | Elastic pendulum | — |
| `example_feedback.pvm` | Feedback system | — |
| `example_filters.pvm` | Filter examples | — |
| `example_harmonic_oscillator.pvm` | Harmonic oscillator | — |
| `example_kalman_filter.pvm` | Kalman filter | — |
| `example_nested_subsystems.pvm` | Nested subsystems | — |
| `example_noise.pvm` | Noise source | — |
| `example_pendulum.pvm` | Pendulum | — |
| `example_phasenoise.pvm` | Phase noise | — |
| `example_pid.pvm` | PID controller | — |
| `example_pid_antiwindup.pvm` | PID with anti-windup | — |
| `example_pid_vs_discretePID.pvm` | PID comparison | — |
| `example_radar.pvm` | Radar system | — |
| `example_reactor.pvm` | Chemical reactor | — |
| `example_solar.pvm` | Solar system model | — |
| `example_solver_hotswap.pvm` | Solver hot-swap | — |
| `example_spectrum.pvm` | Spectrum analysis | — |
| `example_spectrum_rf_oneport.pvm` | RF one-port spectrum | — |
| `example_steadystate.pvm` | Steady-state analysis | — |
| `example_stickslip.pvm` | Stick-slip friction | — |
| `example_transferfunction.pvm` | Transfer function | — |
| `example_vanderpol_subsystem.pvm` | Van der Pol oscillator | — |

### Rebuilding all PVMs

If the converter is updated, rebuild all PVM files:

```bash
python py_to_pvm.py pathsim-master/examples --batch --recursive --skip-missing-deps --quiet --pathsim-root ./pathsim-master
```

---

## Troubleshooting

### Conversion fails with ImportError

The input script imports a module not installed locally. Either:

- Install the missing dependency: `pip install <module>`
- Use `--skip-missing-deps` in batch mode to skip that file

### Conversion fails with "No Simulation object found"

The script does not create a `Simulation` instance, or creates it conditionally (e.g., inside `if __name__ == "__main__"`). Move the `Simulation(...)` call to module-level scope.

### PVM loads in PathView but simulation fails

1. Check the browser console (F12) for the specific error
2. Common causes:
   - Missing import in `codeContext` — rebuild with current converter
   - Parameter type mismatch — check param expressions in the PVM JSON
   - Version mismatch — server PathSim may differ from local

### Streaming stops mid-simulation

- The simulation may have diverged (NaN/Inf values)
- Try reducing `duration` or `dt`
- Check if the solver is appropriate for the model (stiff systems need implicit solvers)

---

## Version Info

- **Converter:** `py_to_pvm.py` (AST-based, supports PathSim 0.20.0+)
- **PathView:** 0.8.6+
- **PVM Format:** 1.0.0
