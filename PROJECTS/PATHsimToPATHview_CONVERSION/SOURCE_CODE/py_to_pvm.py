#!/usr/bin/env python3
"""Convert a PathSim Python model script into a PathView .pvm file.

This converter executes the input script as a module, introspects the resulting
Simulation object, and writes a PathView-compatible .pvm JSON file.

Usage:
  python py_to_pvm.py input_model.py -o output_model.pvm
  python py_to_pvm.py input_model.py --sim-var Sim --pathsim-root ./pathsim-master
    python py_to_pvm.py examples --batch --recursive --skip-missing-deps
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import datetime as dt
import importlib.util
import io
import inspect
import json
import re
import sys
import types
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert PathSim .py to PathView .pvm",
        epilog=(
            "Examples:\n"
            "  python py_to_pvm.py model.py -o model.pvm\n"
            "  python py_to_pvm.py examples --batch --pathsim-root ./pathsim-master\n"
            "  python py_to_pvm.py examples --batch --recursive --skip-missing-deps --quiet"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Path to PathSim Python model file or a directory of files")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .pvm path for a file, or output directory for batch mode")
    parser.add_argument("--sim-var", default=None, help="Name of Simulation variable in module globals")
    parser.add_argument("--name", default=None, help="Model name for metadata")
    parser.add_argument(
        "--pathsim-root",
        type=Path,
        default=None,
        help="Path to local pathsim repo root (its src folder is added to sys.path)",
    )
    parser.add_argument(
        "--code-context",
        choices=["auto", "full", "none"],
        default="auto",
        help="How to populate codeContext.code",
    )
    parser.add_argument(
        "--duration",
        default=None,
        help="Override simulation duration in .pvm (Python expression as string)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Convert all .py files in the input directory",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search for .py files when using directory input",
    )
    parser.add_argument(
        "--skip-missing-deps",
        action="store_true",
        help="Skip files that fail due to missing optional imports in the input model",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress converter progress output and output from imported model scripts",
    )
    return parser.parse_args()


def is_missing_dependency_error(exc: BaseException) -> bool:
    current: Optional[BaseException] = exc
    while current is not None:
        if isinstance(current, (ImportError, ModuleNotFoundError)):
            return True
        current = current.__cause__ or current.__context__
    return False


def iter_input_files(input_path: Path, recursive: bool) -> List[Path]:
    if input_path.is_file():
        return [input_path]

    pattern = "**/*.py" if recursive else "*.py"
    return sorted(path for path in input_path.glob(pattern) if path.is_file())


def resolve_output_path(input_file: Path, input_root: Path, output_arg: Optional[Path], batch_mode: bool) -> Path:
    if not batch_mode:
        return output_arg.resolve() if output_arg else input_file.with_suffix(".pvm")

    if output_arg is None:
        return input_file.with_suffix(".pvm")

    output_root = output_arg.resolve()
    rel_path = input_file.resolve().relative_to(input_root.resolve())
    return output_root / rel_path.with_suffix(".pvm")


def convert_file(
    input_file: Path,
    output_file: Path,
    args: argparse.Namespace,
) -> Path:
    capture = contextlib.ExitStack()
    with capture:
        if args.quiet:
            capture.enter_context(contextlib.redirect_stdout(io.StringIO()))
            capture.enter_context(contextlib.redirect_stderr(io.StringIO()))

        add_import_paths(input_file, args.pathsim_root)
        module = load_module_from_file(input_file)

        Simulation, _Block, _Event = import_pathsim_types()
        sim, sim_var_name = find_simulation(module, args.sim_var, Simulation)

        source_text = input_file.read_text(encoding="utf-8")
        model_name = args.name or input_file.stem

        pvm = build_pvm(
            source_text=source_text,
            model_name=model_name,
            sim_var_name=sim_var_name,
            sim=sim,
            module=module,
            code_context_mode=args.code_context,
            duration_override=args.duration,
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(pvm, indent=2), encoding="utf-8")
    return output_file


def add_import_paths(input_file: Path, pathsim_root: Optional[Path]) -> None:
    input_dir = str(input_file.parent.resolve())
    if input_dir not in sys.path:
        sys.path.insert(0, input_dir)

    if pathsim_root is not None:
        root = pathsim_root.resolve()
        src = root / "src"
        if src.exists():
            src_str = str(src)
            if src_str not in sys.path:
                sys.path.insert(0, src_str)
        else:
            root_str = str(root)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)


def load_module_from_file(py_file: Path) -> types.ModuleType:
    mod_name = f"py_to_pvm_input_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, str(py_file))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec from: {py_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def import_pathsim_types() -> Tuple[type, type, type]:
    from pathsim.simulation import Simulation
    from pathsim.blocks._block import Block
    from pathsim.events._event import Event

    return Simulation, Block, Event


def find_simulation(module: types.ModuleType, sim_var: Optional[str], Simulation: type) -> Tuple[Any, str]:
    if sim_var:
        sim = getattr(module, sim_var, None)
        if sim is None:
            raise ValueError(f"Simulation variable '{sim_var}' not found in input module")
        if not isinstance(sim, Simulation):
            raise TypeError(f"Variable '{sim_var}' exists but is not a pathsim.Simulation")
        return sim, sim_var

    sims: List[Tuple[str, Any]] = []
    for name, value in vars(module).items():
        if isinstance(value, Simulation):
            sims.append((name, value))

    if not sims:
        raise ValueError("No pathsim.Simulation instance found in module globals")

    if len(sims) == 1:
        return sims[0][1], sims[0][0]

    for preferred in ("Sim", "sim", "simulation"):
        for name, value in sims:
            if name == preferred:
                return value, name

    return sims[0][1], sims[0][0]


# Names that become Python builtins/keywords when lowercased by PathView's Or()
# function. Using these as PVM node IDs causes variable shadowing at runtime.
_PATHVIEW_RESERVED_LOWER = frozenset({
    # Python keywords
    "true", "false", "none", "and", "or", "not", "in", "is", "if", "else",
    "elif", "for", "while", "def", "class", "return", "yield", "import",
    "from", "as", "try", "except", "finally", "with", "lambda", "pass",
    "break", "continue", "raise", "global", "nonlocal", "assert", "del",
    # Python builtins commonly used in generated code
    "print", "len", "range", "list", "dict", "set", "tuple", "str", "int",
    "float", "bool", "type", "abs", "min", "max", "sum", "any", "all",
    "map", "filter", "zip", "enumerate", "log", "exp", "sqrt", "sin",
    "cos", "tan", "pi", "np", "numpy", "math",
})


def safe_name(s: str) -> str:
    s = re.sub(r"\W+", "_", s)
    if not s:
        s = "node"
    if s[0].isdigit():
        s = f"n_{s}"
    # PathView lowercases variable names; avoid shadowing Python builtins
    if s.lower() in _PATHVIEW_RESERVED_LOWER:
        s = f"{s}_"
    return s


def ensure_unique(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    i = 2
    while f"{base}_{i}" in used:
        i += 1
    out = f"{base}_{i}"
    used.add(out)
    return out


def infer_object_names(module: types.ModuleType, objs: Sequence[Any], prefix: str) -> Dict[int, str]:
    by_id: Dict[int, str] = {}
    candidates: Dict[int, List[str]] = {}

    for name, value in vars(module).items():
        oid = id(value)
        candidates.setdefault(oid, []).append(name)

    for i, obj in enumerate(objs, start=1):
        oid = id(obj)
        names = candidates.get(oid, [])
        filtered = [n for n in names if not n.startswith("_")]
        chosen = None
        if filtered:
            chosen = sorted(filtered, key=lambda x: (len(x), x))[0]
        elif names:
            chosen = sorted(names, key=lambda x: (len(x), x))[0]
        else:
            chosen = f"{prefix}_{i}"
        by_id[oid] = chosen

    return by_id


def callable_to_expr(fn: Any) -> str:
    if hasattr(fn, "__name__") and fn.__name__ != "<lambda>":
        return fn.__name__

    try:
        src = inspect.getsource(fn).strip()
        if "lambda" in src:
            match = re.search(r"lambda\b.*", src, re.DOTALL)
            if match:
                raw = match.group(0).strip()
                # The regex grabs everything after "lambda", which may include
                # trailing chars from an enclosing call, e.g.  Source(lambda t: f(t))
                # where the last ')' belongs to Source(), not the lambda body.
                # Progressively strip trailing unbalanced parens/commas until
                # the expression is syntactically valid.
                expr = raw
                while expr:
                    try:
                        ast.parse(expr, mode="eval")
                        return expr
                    except SyntaxError:
                        stripped = expr.rstrip()
                        if stripped and stripped[-1] in "),":
                            expr = stripped[:-1]
                        else:
                            break
                return raw
        if src.startswith("def "):
            m = re.match(r"def\s+([A-Za-z_]\w*)\s*\(", src)
            if m:
                return m.group(1)
    except Exception:
        pass

    return "lambda *args, **kwargs: 0"


def _expr_references_names(expr_str: str, names: set) -> bool:
    """Return True if *expr_str* contains a reference to any name in *names*."""
    try:
        tree = ast.parse(expr_str, mode="eval")
    except Exception:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in names:
            return True
    return False


def value_to_expr(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return repr(value)
    if callable(value):
        return callable_to_expr(value)

    if np is not None and isinstance(value, np.ndarray):
        return f"np.array({value.tolist()!r})"

    if isinstance(value, (list, tuple, dict, set)):
        return repr(value)

    return repr(value)


def resolve_expr_to_setting(expr: Any, module: types.ModuleType) -> str:
    """Resolve expression/string to a concrete setting string when possible.

    PathView streaming is more robust when `dt` and `duration` are numeric literals
    instead of symbolic names that rely on external evaluation context.
    """
    if isinstance(expr, (int, float, bool)):
        return str(expr)

    if isinstance(expr, str):
        text = expr.strip()
        if not text:
            return ""
        try:
            value = eval(text, vars(module), vars(module))
        except Exception:
            return text
    else:
        value = expr

    if np is not None and isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, (int, float, bool)):
        return str(value)

    return str(expr) if expr is not None else ""


def get_block_param_names(block: Any) -> List[str]:
    try:
        info = block.__class__.info()
        params = info.get("parameters", {})
        return list(params.keys())
    except Exception:
        return []


def get_block_param_defaults(block: Any) -> Dict[str, Any]:
    try:
        info = block.__class__.info()
        params = info.get("parameters", {})
        return {k: v.get("default") for k, v in params.items()}
    except Exception:
        return {}


def get_event_param_names(event: Any) -> List[str]:
    try:
        sig = inspect.signature(event.__class__.__init__)
        out = []
        for name, p in sig.parameters.items():
            if name in ("self", "args", "kwargs"):
                continue
            if p.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
                continue
            out.append(name)
        return out
    except Exception:
        return []


def normalize_ports(port_ref: Any, is_input: bool) -> List[int]:
    block = port_ref.block
    out: List[int] = []
    for p in port_ref.ports:
        if isinstance(p, int):
            out.append(p)
        else:
            mapped = block.inputs._map(p) if is_input else block.outputs._map(p)
            if not isinstance(mapped, int):
                raise ValueError(f"Could not map port alias '{p}' on block {block}")
            out.append(mapped)
    return out


def infer_base_port_count(block: Any, direction: str) -> Optional[int]:
    labels = block.__class__.input_port_labels if direction == "input" else block.__class__.output_port_labels
    if labels == {}:
        return 0
    if isinstance(labels, dict) and labels:
        max_idx = max(int(v) for v in labels.values())
        return max_idx + 1
    return None


def infer_label_map(block: Any, direction: str) -> Dict[int, str]:
    labels = block.__class__.input_port_labels if direction == "input" else block.__class__.output_port_labels
    if not isinstance(labels, dict):
        return {}
    return {int(v): str(k) for k, v in labels.items()}


def build_ports(node_id: str, direction: str, count: int, label_map: Dict[int, str]) -> List[Dict[str, Any]]:
    ports = []
    for i in range(count):
        default_name = f"in {i}" if direction == "input" else f"out {i}"
        name = label_map.get(i, default_name)
        ports.append(
            {
                "id": f"{node_id}-{direction}-{i}",
                "nodeId": node_id,
                "name": name,
                "direction": direction,
                "index": i,
                "color": "#969696",
            }
        )
    return ports


def infer_vector_length_from_expr(expr: Any) -> int:
    if not isinstance(expr, str):
        return 0

    text = expr.strip()
    if not text:
        return 0

    candidate = text
    if text.startswith("np.array(") and text.endswith(")"):
        candidate = text[len("np.array(") : -1].strip()

    try:
        value = ast.literal_eval(candidate)
    except Exception:
        return 0

    if isinstance(value, (list, tuple)) and value:
        first = value[0]
        if isinstance(first, (list, tuple)):
            return len(first)
        return len(value)

    return 0


def infer_vector_length_from_runtime(block: Any) -> int:
    candidates = [
        getattr(block, "initial_value", None),
        getattr(block, "x", None),
        getattr(block, "x0", None),
        getattr(block, "state", None),
    ]

    for value in candidates:
        if value is None:
            continue
        if np is not None and isinstance(value, np.ndarray):
            flat = np.ravel(value)
            if flat.size > 1:
                return int(flat.size)
        if isinstance(value, (list, tuple)) and len(value) > 1:
            return len(value)

    return 0


def normalize_vector_scope_connections(
    pvm_nodes: List[Dict[str, Any]],
    pvm_connections: List[Dict[str, Any]],
    vector_len_hints: Dict[str, int],
) -> bool:
    node_by_id: Dict[str, Dict[str, Any]] = {str(n["id"]): n for n in pvm_nodes}
    used_ids: set[str] = {str(n["id"]) for n in pvm_nodes}
    made_changes = False

    # Only rewrite the simple direct case where a vector signal is sent into
    # a single-input Scope channel.
    while True:
        candidate_idx: Optional[int] = None
        candidate_vec_len = 0
        candidate_scalarize = False
        candidate_scope: Optional[Dict[str, Any]] = None
        candidate_src: Optional[Dict[str, Any]] = None

        for idx, conn in enumerate(pvm_connections):
            src = node_by_id.get(str(conn.get("sourceNodeId", "")))
            trg = node_by_id.get(str(conn.get("targetNodeId", "")))
            if not src or not trg:
                continue
            if trg.get("type") != "Scope":
                continue
            if len(src.get("outputs", []) or []) != 1:
                continue

            src_id = str(src.get("id", ""))
            if "_demux_" in src_id or "_scalar_" in src_id:
                continue

            incoming = [c for c in pvm_connections if c.get("targetNodeId") == trg.get("id")]
            if len(incoming) != 1:
                continue
            if len(trg.get("inputs", []) or []) != 1:
                continue

            params = src.get("params", {}) or {}
            vec_len = int(vector_len_hints.get(str(src.get("id", "")), 0))
            if vec_len <= 1:
                vec_len = infer_vector_length_from_expr(params.get("initial_value", ""))

            # Unknown dimensionality can still produce a vector at runtime.
            # In that case insert a scalarizer to ensure Scope receives scalars.
            scalarize = vec_len <= 1

            candidate_idx = idx
            candidate_vec_len = vec_len
            candidate_scalarize = scalarize
            candidate_scope = trg
            candidate_src = src
            break

        if candidate_idx is None or candidate_scope is None or candidate_src is None:
            break

        old_conn = pvm_connections.pop(candidate_idx)
        src_id = str(old_conn["sourceNodeId"])
        scope_id = str(old_conn["targetNodeId"])

        if candidate_scalarize:
            raw_id = f"{src_id}_scalar_0"
            scalar_id = ensure_unique(safe_name(raw_id), used_ids)
            base_pos = candidate_src.get("position", {"x": 180, "y": 120})
            scalar_node = {
                "id": scalar_id,
                "type": "Function",
                "name": f"{candidate_src.get('name', src_id)}_scalar",
                "position": {
                    "x": int(base_pos.get("x", 180)) + 220,
                    "y": int(base_pos.get("y", 120)),
                },
                "inputs": build_ports(scalar_id, "input", 1, {}),
                "outputs": build_ports(scalar_id, "output", 1, {}),
                "params": {"func": "lambda x: _pv_scalar(x, 0)"},
            }
            pvm_nodes.append(scalar_node)
            node_by_id[scalar_id] = scalar_node

            pvm_connections.append(
                {
                    "id": "",
                    "sourceNodeId": src_id,
                    "sourcePortIndex": 0,
                    "targetNodeId": scalar_id,
                    "targetPortIndex": 0,
                }
            )
            pvm_connections.append(
                {
                    "id": "",
                    "sourceNodeId": scalar_id,
                    "sourcePortIndex": 0,
                    "targetNodeId": scope_id,
                    "targetPortIndex": 0,
                }
            )

            made_changes = True
            continue

        candidate_scope["inputs"] = build_ports(
            scope_id,
            "input",
            int(candidate_vec_len),
            {},
        )

        base_pos = candidate_src.get("position", {"x": 180, "y": 120})
        start_y = int(base_pos.get("y", 120)) - 25 * (candidate_vec_len - 1)

        for comp_idx in range(candidate_vec_len):
            raw_id = f"{src_id}_demux_{comp_idx}"
            demux_id = ensure_unique(safe_name(raw_id), used_ids)
            demux_node = {
                "id": demux_id,
                "type": "Function",
                "name": f"{candidate_src.get('name', src_id)}_demux_{comp_idx}",
                "position": {
                    "x": int(base_pos.get("x", 180)) + 220,
                    "y": start_y + 50 * comp_idx,
                },
                "inputs": build_ports(demux_id, "input", 1, {}),
                "outputs": build_ports(demux_id, "output", 1, {}),
                "params": {"func": f"lambda x: _pv_scalar(x, {comp_idx})"},
            }
            pvm_nodes.append(demux_node)
            node_by_id[demux_id] = demux_node

            pvm_connections.append(
                {
                    "id": "",
                    "sourceNodeId": src_id,
                    "sourcePortIndex": 0,
                    "targetNodeId": demux_id,
                    "targetPortIndex": 0,
                }
            )
            pvm_connections.append(
                {
                    "id": "",
                    "sourceNodeId": demux_id,
                    "sourcePortIndex": 0,
                    "targetNodeId": scope_id,
                    "targetPortIndex": comp_idx,
                }
            )

        made_changes = True

    for idx, conn in enumerate(pvm_connections, start=1):
        conn["id"] = f"conn-{idx:04d}"

    return made_changes


def normalize_stream_target_scalar_inputs(
    pvm_nodes: List[Dict[str, Any]],
    pvm_connections: List[Dict[str, Any]],
) -> bool:
    node_by_id: Dict[str, Dict[str, Any]] = {str(n["id"]): n for n in pvm_nodes}
    used_ids: set[str] = {str(n["id"]) for n in pvm_nodes}
    made_changes = False

    stream_target_types = {"Scope", "RealtimeScope", "Spectrum"}
    rewritten: List[Dict[str, Any]] = []

    for conn in pvm_connections:
        src = node_by_id.get(str(conn.get("sourceNodeId", "")))
        trg = node_by_id.get(str(conn.get("targetNodeId", "")))
        if not src or not trg:
            rewritten.append(conn)
            continue

        if trg.get("type") not in stream_target_types:
            rewritten.append(conn)
            continue

        src_id = str(src.get("id", ""))
        if "_scalar_" in src_id or "_demux_" in src_id:
            rewritten.append(conn)
            continue

        # Only scalarize single-output sources; multi-output sources are already
        # port-indexed and should remain untouched.
        if len(src.get("outputs", []) or []) != 1:
            rewritten.append(conn)
            continue

        scalar_id = ensure_unique(safe_name(f"{src_id}_scalar_{conn.get('targetPortIndex', 0)}"), used_ids)
        src_pos = src.get("position", {"x": 180, "y": 120})
        trg_pos = trg.get("position", {"x": int(src_pos.get("x", 180)) + 220, "y": int(src_pos.get("y", 120))})

        scalar_node = {
            "id": scalar_id,
            "type": "Function",
            "name": f"{src.get('name', src_id)}_scalar_{conn.get('targetPortIndex', 0)}",
            "position": {
                "x": int((int(src_pos.get("x", 180)) + int(trg_pos.get("x", 400))) / 2),
                "y": int((int(src_pos.get("y", 120)) + int(trg_pos.get("y", 120))) / 2),
            },
            "inputs": build_ports(scalar_id, "input", 1, {}),
            "outputs": build_ports(scalar_id, "output", 1, {}),
            "params": {"func": "lambda x: _pv_scalar(x, 0)"},
        }

        pvm_nodes.append(scalar_node)
        node_by_id[scalar_id] = scalar_node

        rewritten.append(
            {
                "id": "",
                "sourceNodeId": conn.get("sourceNodeId"),
                "sourcePortIndex": conn.get("sourcePortIndex", 0),
                "targetNodeId": scalar_id,
                "targetPortIndex": 0,
            }
        )
        rewritten.append(
            {
                "id": "",
                "sourceNodeId": scalar_id,
                "sourcePortIndex": 0,
                "targetNodeId": conn.get("targetNodeId"),
                "targetPortIndex": conn.get("targetPortIndex", 0),
            }
        )
        made_changes = True

    if made_changes:
        pvm_connections[:] = rewritten
        for idx, c in enumerate(pvm_connections, start=1):
            c["id"] = f"conn-{idx:04d}"

    return made_changes


def normalize_source_like_scalar_outputs(
    pvm_nodes: List[Dict[str, Any]],
    pvm_connections: List[Dict[str, Any]],
) -> bool:
    node_by_id: Dict[str, Dict[str, Any]] = {str(n["id"]): n for n in pvm_nodes}
    used_ids: set[str] = {str(n["id"]) for n in pvm_nodes}
    made_changes = False

    # These source-like blocks can produce non-scalar payloads in PathView runtime.
    # Insert scalarizers once at their output fanout root.
    source_like_types = {"ChirpPhaseNoiseSource"}

    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for conn in pvm_connections:
        src_id = str(conn.get("sourceNodeId", ""))
        by_source.setdefault(src_id, []).append(conn)

    rewritten: List[Dict[str, Any]] = []
    inserted_for: set[str] = set()

    for conn in pvm_connections:
        src_id = str(conn.get("sourceNodeId", ""))
        src = node_by_id.get(src_id)
        if not src:
            rewritten.append(conn)
            continue

        if src.get("type") not in source_like_types:
            rewritten.append(conn)
            continue
        if len(src.get("outputs", []) or []) != 1:
            rewritten.append(conn)
            continue
        if "_scalar_" in src_id or "_demux_" in src_id:
            rewritten.append(conn)
            continue

        scalar_id = f"{src_id}_scalar_out"
        if src_id not in inserted_for:
            scalar_id = ensure_unique(safe_name(scalar_id), used_ids)
            src_pos = src.get("position", {"x": 180, "y": 120})
            scalar_node = {
                "id": scalar_id,
                "type": "Function",
                "name": f"{src.get('name', src_id)}_scalar_out",
                "position": {
                    "x": int(src_pos.get("x", 180)) + 140,
                    "y": int(src_pos.get("y", 120)),
                },
                "inputs": build_ports(scalar_id, "input", 1, {}),
                "outputs": build_ports(scalar_id, "output", 1, {}),
                "params": {"func": "lambda x: _pv_scalar(x, 0)"},
            }
            pvm_nodes.append(scalar_node)
            node_by_id[scalar_id] = scalar_node

            # Add the source->scalar edge only once.
            rewritten.append(
                {
                    "id": "",
                    "sourceNodeId": src_id,
                    "sourcePortIndex": 0,
                    "targetNodeId": scalar_id,
                    "targetPortIndex": 0,
                }
            )
            inserted_for.add(src_id)
            made_changes = True

            # Retarget all fanout edges from source to scalar.
            for fan in by_source.get(src_id, []):
                rewritten.append(
                    {
                        "id": "",
                        "sourceNodeId": scalar_id,
                        "sourcePortIndex": 0,
                        "targetNodeId": fan.get("targetNodeId"),
                        "targetPortIndex": fan.get("targetPortIndex", 0),
                    }
                )

            # Skip original fanout edges by not appending current conn.
            continue

        # If already inserted for this source, original fanout edge is skipped.
        if src_id in inserted_for:
            continue

        rewritten.append(conn)

    if made_changes:
        # Remove possible duplicates while preserving order.
        seen: set[tuple[str, int, str, int]] = set()
        deduped: List[Dict[str, Any]] = []
        for c in rewritten:
            key = (
                str(c.get("sourceNodeId", "")),
                int(c.get("sourcePortIndex", 0)),
                str(c.get("targetNodeId", "")),
                int(c.get("targetPortIndex", 0)),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(c)

        pvm_connections[:] = deduped
        for idx, c in enumerate(pvm_connections, start=1):
            c["id"] = f"conn-{idx:04d}"

    return made_changes


def extract_code_context_auto(source: str, excluded_names: set[str], ctor_names: set[str], sim_var: str = "sim") -> str:
    try:
        tree = ast.parse(source)
    except Exception:
        return source

    # Find the index of sim_var.run() — everything from that point on is
    # post-simulation analysis / plotting and must NOT appear in codeContext.
    cutoff_index = len(tree.body)
    for idx, node in enumerate(tree.body):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            fn = node.value.func
            if (isinstance(fn, ast.Attribute) and fn.attr == "run"
                    and isinstance(fn.value, ast.Name) and fn.value.id == sim_var):
                cutoff_index = idx
                break

    kept: List[ast.stmt] = []

    def references_excluded(node: ast.AST) -> bool:
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and n.id in excluded_names:
                return True
        return False

    def is_constructor_call_assignment(node: ast.stmt) -> bool:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            return False
        fn = node.value.func
        if isinstance(fn, ast.Name):
            if fn.id in ctor_names:
                return True
        elif isinstance(fn, ast.Attribute):
            if fn.attr in ctor_names:
                return True
        return False

    def is_subsystem_list_assignment(node: ast.stmt) -> bool:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.List):
            return False
        # Identify blocks lists meant for Subsystem (e.g., sub_blocks = [If, I1, I2...])
        names = []
        for e in node.value.elts:
            if isinstance(e, ast.Name):
                names.append(e.id)
        if any(n in excluded_names for n in names):
            return True
        return False

    for body_idx, node in enumerate(tree.body):
        # Skip everything at or after sim.run() — post-simulation code
        if body_idx >= cutoff_index:
            continue

        if isinstance(node, ast.If):
            if isinstance(node.test, ast.Compare):
                left = node.test.left
                if isinstance(left, ast.Name) and left.id == "__name__":
                    continue

        if references_excluded(node):
            continue
        if is_constructor_call_assignment(node):
            # Also add the variable to excluded_names so that it is properly excluded later
            for t in node.targets:
                if isinstance(t, ast.Name):
                    excluded_names.add(t.id)
            continue
        if is_subsystem_list_assignment(node):
            continue

        if isinstance(node, ast.ImportFrom):
            pass # Keep all imports so internal Subsystem blocks evaluate successfully in worker
        if isinstance(node, ast.Import):
            pass # Keep all imports

        kept.append(node)

    if not kept:
        return ""

    chunks = []
    for node in kept:
        try:
            chunks.append(ast.unparse(node))
        except Exception:
            pass

    return "\n\n".join(chunks).strip()


def detect_duration_expr(source: str, sim_var: str) -> Optional[str]:
    try:
        tree = ast.parse(source)
    except Exception:
        return None

    class RunVisitor(ast.NodeVisitor):
        found: Optional[str] = None

        def visit_Call(self, node: ast.Call) -> Any:
            if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == sim_var:
                    if node.args and self.found is None:
                        try:
                            self.found = ast.unparse(node.args[0])
                            return
                        except Exception:
                            pass
            self.generic_visit(node)

    v = RunVisitor()
    v.visit(tree)
    return v.found


def get_constructor_param_order(class_name: str, blocks: Sequence[Any], events: Sequence[Any]) -> List[str]:
    for block in blocks:
        if block.__class__.__name__ == class_name:
            return get_block_param_names(block)
    for event in events:
        if event.__class__.__name__ == class_name:
            return get_event_param_names(event)
    return []


def extract_ctor_param_exprs(
    source: str,
    ctor_names: set[str],
    blocks: Sequence[Any],
    events: Sequence[Any],
) -> Dict[str, Dict[str, str]]:
    """Map variable name -> constructor arg expressions from source AST."""
    out: Dict[str, Dict[str, str]] = {}

    try:
        tree = ast.parse(source)
    except Exception:
        return out

    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if not isinstance(node.value, ast.Call):
            continue

        fn = node.value.func
        ctor_name = None
        if isinstance(fn, ast.Name):
            ctor_name = fn.id
        elif isinstance(fn, ast.Attribute):
            ctor_name = fn.attr

        if ctor_name not in ctor_names:
            continue

        param_order = get_constructor_param_order(ctor_name, blocks, events)
        arg_map: Dict[str, str] = {}

        for index, arg in enumerate(node.value.args):
            if index >= len(param_order):
                break
            try:
                arg_map[param_order[index]] = ast.unparse(arg)
            except Exception:
                continue

        for kw in node.value.keywords:
            if kw.arg is None:
                continue
            try:
                arg_map[kw.arg] = ast.unparse(kw.value)
            except Exception:
                continue

        out[target.id] = arg_map

    return out


def position_for(index: int, cols: int = 5, x0: int = 180, y0: int = 120, dx: int = 220, dy: int = 140) -> Dict[str, int]:
    row = index // cols
    col = index % cols
    return {"x": x0 + col * dx, "y": y0 + row * dy}


def build_subsystem_graph(
    subsystem: Any,
    module: types.ModuleType,
    source_text: str,
    source_ctor_kw: Dict[str, Dict[str, str]],
) -> Dict[str, Any]:
    """Build a PVM ``graph`` sub-structure for a Subsystem node.

    PathView's frontend code-generator (``Ih`` / ``generateSubsystemCode``)
    reads ``node.graph.{nodes, connections, events}`` to build the Python
    exec string. It completely ignores Subsystem ``params``.
    """
    from pathsim.subsystem import Subsystem as _Sub

    iface = subsystem.interface           # single Interface block
    internal_blocks = list(subsystem.blocks)  # all blocks except Interface
    internal_conns = list(subsystem.connections)
    all_events = list(getattr(subsystem, "events", []))

    # Filter out events that are auto-created by blocks (e.g. WhiteNoise's
    # internal Schedule events whose func_act is a bound closure like
    # WhiteNoise.__init__.<locals>._set).  These get re-created when the
    # block itself is instantiated, so putting them in the graph would cause
    # duplicates AND fail because the closure can't be referenced by name.
    internal_events = [
        evt for evt in all_events
        if not callable(getattr(evt, "func_act", None))
    ]

    # --- variable-name lookup via the module namespace ---
    all_internal = [iface] + internal_blocks
    int_var_map = infer_object_names(module, all_internal, prefix="sub_block")

    used_ids: set[str] = set()
    int_id_map: Dict[int, str] = {}
    for obj in all_internal:
        base = safe_name(int_var_map[id(obj)])
        int_id_map[id(obj)] = ensure_unique(base, used_ids)

    # --- child nodes ---
    child_nodes: List[Dict[str, Any]] = []
    for j, blk in enumerate(all_internal):
        nid = int_id_map[id(blk)]
        ntype = blk.__class__.__name__

        base_in = infer_base_port_count(blk, "input")
        base_out = infer_base_port_count(blk, "output")
        in_count = base_in if base_in is not None else max(len(blk.inputs), 1)
        out_count = base_out if base_out is not None else max(len(blk.outputs), 1)

        in_labels = infer_label_map(blk, "input")
        out_labels = infer_label_map(blk, "output")

        params: Dict[str, Any] = {}
        _sub_block_var_names = set(int_var_map.values())
        # Skip params for Interface (none) and nested Subsystem (handled via recursion)
        if ntype not in ("Interface", "Subsystem"):
            src_name = int_var_map[id(blk)]
            src_kw = source_ctor_kw.get(src_name, {})
            defaults = get_block_param_defaults(blk)
            for p in get_block_param_names(blk):
                if p in src_kw:
                    expr = src_kw[p]
                    if _expr_references_names(expr, _sub_block_var_names - {int_var_map[id(blk)]}):
                        if hasattr(blk, p):
                            v = value_to_expr(getattr(blk, p))
                            params[p] = str(v) if not isinstance(v, str) else v
                        else:
                            params[p] = expr
                    else:
                        params[p] = expr
                elif not src_kw and hasattr(blk, p):
                    value = getattr(blk, p)
                    default = defaults.get(p)
                    try:
                        import numpy as np
                        if isinstance(value, np.ndarray) or isinstance(default, np.ndarray):
                            different = not np.array_equal(value, default)
                        else:
                            different = bool(value != default)
                    except Exception:
                        different = True
                    if different:
                        params[p] = value_to_expr(value)

        node_dict: Dict[str, Any] = {
            "id": nid,
            "type": ntype,
            "name": int_var_map[id(blk)],
            "position": position_for(j, x0=100, y0=100),
            "inputs": build_ports(nid, "input", int(in_count), in_labels),
            "outputs": build_ports(nid, "output", int(out_count), out_labels),
            "params": params,
        }

        # Recurse for nested Subsystems
        if isinstance(blk, _Sub):
            node_dict["graph"] = build_subsystem_graph(
                blk, module, source_text, source_ctor_kw,
            )

        child_nodes.append(node_dict)

    # --- child connections ---
    child_conns: List[Dict[str, Any]] = []
    cidx = 1
    for conn in internal_conns:
        src = conn.source
        src_block = src.block
        src_ports = normalize_ports(src, is_input=False)

        for trg in conn.targets:
            trg_block = trg.block
            trg_ports = normalize_ports(trg, is_input=True)
            for sp, tp in zip(src_ports, trg_ports):
                child_conns.append({
                    "id": f"sub-conn-{cidx:04d}",
                    "sourceNodeId": int_id_map[id(src_block)],
                    "sourcePortIndex": int(sp),
                    "targetNodeId": int_id_map[id(trg_block)],
                    "targetPortIndex": int(tp),
                })
                cidx += 1

    # --- child events ---
    child_events: List[Dict[str, Any]] = []
    evt_var_map = infer_object_names(module, internal_events, prefix="sub_event")
    for k, evt in enumerate(internal_events):
        etype = evt.__class__.__name__
        if evt.__class__.__module__.startswith("pathsim.events"):
            etype_full = f"pathsim.events.{etype}"
        else:
            etype_full = f"{evt.__class__.__module__}.{etype}"
        eparams: Dict[str, Any] = {}
        src_name = evt_var_map[id(evt)]
        src_kw = source_ctor_kw.get(src_name, {})
        for p in get_event_param_names(evt):
            if p in src_kw:
                eparams[p] = src_kw[p]
            elif not src_kw and hasattr(evt, p):
                eparams[p] = value_to_expr(getattr(evt, p))
        child_events.append({
            "id": f"sub-evt-{k+1:03d}",
            "type": etype_full,
            "name": evt_var_map[id(evt)],
            "position": {"x": 100 + k * 220, "y": 80},
            "params": eparams,
        })

    return {
        "nodes": child_nodes,
        "connections": child_conns,
        "events": child_events,
    }


def build_pvm(
    source_text: str,
    model_name: str,
    sim_var_name: str,
    sim: Any,
    module: types.ModuleType,
    code_context_mode: str,
    duration_override: Optional[str],
) -> Dict[str, Any]:
    blocks = list(sim.blocks)
    events = list(sim.events)
    connections = list(sim.connections)

    block_var_map = infer_object_names(module, blocks, prefix="block")
    event_var_map = infer_object_names(module, events, prefix="event")

    ctor_names_for_extract = {
        "Simulation",
        "Connection",
        "Event",
        "Subsystem",
        "ZeroCrossing",
        "ZeroCrossingUp",
        "ZeroCrossingDown",
        "Condition",
        "Schedule",
    }
    # Re-enabled: AST-based extraction is more reliable than inspect+regex
    # (avoids trailing-paren bugs from callable_to_expr).  Top-level names
    # won't collide with subsystem internals because extract_ctor_param_exprs
    # only looks at top-level ast.Assign nodes.
    ctor_names_for_extract.update({b.__class__.__name__ for b in blocks})
    ctor_names_for_extract.update({e.__class__.__name__ for e in events})
    # ctor_names_for_extract.update({e.__class__.__name__ for e in events})
    source_ctor_kw = extract_ctor_param_exprs(source_text, ctor_names_for_extract, blocks, events)
    sim_ctor_kw = source_ctor_kw.get(sim_var_name, {})

    used_node_ids: set[str] = set()
    block_id_map: Dict[int, str] = {}

    for b in blocks:
        base_name = safe_name(block_var_map[id(b)])
        block_id_map[id(b)] = ensure_unique(base_name, used_node_ids)

    used_in_ports: Dict[int, set[int]] = {id(b): set() for b in blocks}
    used_out_ports: Dict[int, set[int]] = {id(b): set() for b in blocks}

    pvm_connections: List[Dict[str, Any]] = []
    cidx = 1
    for conn in connections:
        src = conn.source
        src_block = src.block
        src_ports = normalize_ports(src, is_input=False)

        for trg in conn.targets:
            trg_block = trg.block
            trg_ports = normalize_ports(trg, is_input=True)
            if len(src_ports) != len(trg_ports):
                raise ValueError(
                    f"Connection dimension mismatch: source ports {src_ports} vs target ports {trg_ports}"
                )

            for sp, tp in zip(src_ports, trg_ports):
                used_out_ports[id(src_block)].add(int(sp))
                used_in_ports[id(trg_block)].add(int(tp))
                pvm_connections.append(
                    {
                        "id": f"conn-{cidx:04d}",
                        "sourceNodeId": block_id_map[id(src_block)],
                        "sourcePortIndex": int(sp),
                        "targetNodeId": block_id_map[id(trg_block)],
                        "targetPortIndex": int(tp),
                    }
                )
                cidx += 1

    # Collect all block variable names so we can detect cross-block param
    # references (e.g. f_max=rfntwk.network.frequency.stop) and fall back to
    # serialising the runtime value, which the PathView validator can evaluate
    # without the block object being present in the codeContext namespace.
    _all_block_var_names = set(block_var_map.values())

    pvm_nodes: List[Dict[str, Any]] = []
    vector_len_hints: Dict[str, int] = {}
    for i, block in enumerate(blocks):
        node_id = block_id_map[id(block)]
        node_type = block.__class__.__name__

        # PathView 0.8.4 does not know the RFNetwork block type.  When it
        # encounters an unregistered type it silently drops the node, so the
        # simulation runs without it.  RFNetwork internally computes a
        # state-space model (A, B, C, D) via scikit-rf vector-fitting, so we
        # can transparently emit a StateSpace node instead.
        _rfntwk_replaced = False
        if node_type == "RFNetwork" and all(hasattr(block, m) for m in ("A", "B", "C", "D")):
            node_type = "StateSpace"
            _rfntwk_replaced = True

        base_in = infer_base_port_count(block, "input")
        base_out = infer_base_port_count(block, "output")

        in_count_candidates = [max(used_in_ports[id(block)]) + 1] if used_in_ports[id(block)] else []
        out_count_candidates = [max(used_out_ports[id(block)]) + 1] if used_out_ports[id(block)] else []

        if base_in is None:
            in_count_candidates.append(len(block.inputs))
            in_count = max(in_count_candidates) if in_count_candidates else 1
        else:
            in_count = max([base_in] + in_count_candidates) if in_count_candidates else base_in

        if base_out is None:
            out_count_candidates.append(len(block.outputs))
            out_count = max(out_count_candidates) if out_count_candidates else 1
        else:
            out_count = max([base_out] + out_count_candidates) if out_count_candidates else base_out

        in_labels = infer_label_map(block, "input")
        out_labels = infer_label_map(block, "output")

        params: Dict[str, Any] = {}
        src_name = block_var_map[id(block)]
        src_kw = source_ctor_kw.get(src_name, {})
        defaults = get_block_param_defaults(block)
        for p in get_block_param_names(block):
            if p in src_kw:
                expr = src_kw[p]
                # If the expression references another block variable, the
                # PathView validator cannot resolve it (the block object only
                # exists at simulation time).  Fall back to the runtime value.
                if _expr_references_names(expr, _all_block_var_names - {block_var_map[id(block)]}):
                    if hasattr(block, p):
                        v = value_to_expr(getattr(block, p))
                        params[p] = str(v) if not isinstance(v, str) else v
                    else:
                        params[p] = expr
                else:
                    params[p] = expr
            elif not src_kw and hasattr(block, p):
                # Fallback only when constructor args couldn't be recovered.
                # Avoid serializing defaults/internal state that can break runtime behavior.
                value = getattr(block, p)
                default = defaults.get(p)
                
                try:
                    import numpy as np
                    if isinstance(value, np.ndarray) or isinstance(default, np.ndarray):
                        different = not np.array_equal(value, default)
                    else:
                        different = bool(value != default)
                except Exception:
                    different = True

                if different:
                    params[p] = value_to_expr(value)

        # Override params for RFNetwork → StateSpace conversion
        if _rfntwk_replaced:
            import numpy as _np
            params = {
                "A": f"np.array({_np.array(block.A).tolist()!r})",
                "B": f"np.array({_np.array(block.B).tolist()!r})",
                "C": f"np.array({_np.array(block.C).tolist()!r})",
                "D": f"np.array({_np.array(block.D).tolist()!r})",
            }

        pvm_node = {
                "id": node_id,
                "type": node_type,
                "name": block_var_map[id(block)],
                "position": position_for(i),
                "inputs": build_ports(node_id, "input", int(in_count), in_labels),
                "outputs": build_ports(node_id, "output", int(out_count), out_labels),
                "params": params,
            }

        # For Subsystem nodes, build a proper graph sub-structure.
        # PathView's frontend reads node.graph.{nodes,connections,events}
        # and IGNORES params for Subsystem code generation.
        from pathsim.subsystem import Subsystem as _SubCls
        if isinstance(block, _SubCls):
            pvm_node["graph"] = build_subsystem_graph(
                block, module, source_text, source_ctor_kw,
            )
            # Clear string params that PathView won't use
            pvm_node["params"] = {}

        pvm_nodes.append(pvm_node)
        vector_len_hints[node_id] = infer_vector_length_from_runtime(block)

    pvm_events: List[Dict[str, Any]] = []
    for i, event in enumerate(events):
        params: Dict[str, Any] = {}
        src_name = event_var_map[id(event)]
        src_kw = source_ctor_kw.get(src_name, {})
        for p in get_event_param_names(event):
            if p in src_kw:
                params[p] = src_kw[p]
            elif not src_kw and hasattr(event, p):
                params[p] = value_to_expr(getattr(event, p))

        if event.__class__.__module__.startswith("pathsim.events"):
            evt_type = f"pathsim.events.{event.__class__.__name__}"
        else:
            evt_type = f"{event.__class__.__module__}.{event.__class__.__name__}"
        evt_name = event_var_map[id(event)]
        pvm_events.append(
            {
                "id": f"evt-{i+1:03d}",
                "type": evt_type,
                "name": evt_name,
                "position": {"x": 220 + i * 220, "y": 80},
                "params": params,
            }
        )

    excluded_names = {block_var_map[id(b)] for b in blocks}
    excluded_names.update({event_var_map[id(e)] for e in events})
    excluded_names.update({"blocks", "connections", "events", sim_var_name})

    # Also exclude internal Subsystem block variable names from codeContext.
    # PathView's frontend rebuilds them from the graph sub-structure.
    from pathsim.subsystem import Subsystem as _SubCls2
    for b in blocks:
        if isinstance(b, _SubCls2):
            all_internal = [b.interface] + list(b.blocks)
            int_names = infer_object_names(module, all_internal, prefix="sub_block")
            excluded_names.update(int_names.values())

    if code_context_mode == "none":
        code_context = ""
    elif code_context_mode == "full":
        code_context = source_text
    else:
        # Use the comprehensive ctor_names_for_extract we built earlier
        code_context = extract_code_context_auto(source_text, excluded_names, ctor_names_for_extract, sim_var=sim_var_name)

    # Inject imports for event classes used inside Subsystem graphs.
    # PathView's frontend generates e.g. Schedule(...) from graph.events
    # but the original source may not import them (they're internal to Subsystem).
    sub_event_classes: set[str] = set()
    for node in pvm_nodes:
        if "graph" in node:
            for evt in node["graph"].get("events", []):
                etype = evt.get("type", "")
                # type is like "pathsim.events.Schedule" -> extract "Schedule"
                cls_name = etype.rsplit(".", 1)[-1] if "." in etype else etype
                if cls_name:
                    sub_event_classes.add(cls_name)
    if sub_event_classes:
        missing = [c for c in sorted(sub_event_classes) if c not in code_context]
        if missing:
            import_line = "from pathsim.events import " + ", ".join(missing)
            # Insert right after the last 'from pathsim' import for clean grouping
            lines = code_context.split("\n")
            insert_idx = len(lines)  # fallback: end
            for idx_l, ln in enumerate(lines):
                if ln.startswith("from pathsim"):
                    insert_idx = idx_l + 1
            lines.insert(insert_idx, "")
            lines.insert(insert_idx + 1, import_line)
            code_context = "\n".join(lines)

    demux_added = normalize_vector_scope_connections(pvm_nodes, pvm_connections, vector_len_hints)
    source_scalarize_added = normalize_source_like_scalar_outputs(pvm_nodes, pvm_connections)
    scalarize_added = normalize_stream_target_scalar_inputs(pvm_nodes, pvm_connections)
    if (demux_added or source_scalarize_added or scalarize_added) and "import numpy as np" not in code_context:
        code_context = ("import numpy as np\n\n" + code_context).strip()
    if (demux_added or source_scalarize_added or scalarize_added) and "def _pv_scalar(" not in code_context:
        scalar_helper = (
            "def _pv_scalar(x, idx=0):\n"
            "    # Robustly extract one scalar from nested arrays/lists/tuples.\n"
            "    v = x\n"
            "    target = int(idx)\n"
            "    for _ in range(8):\n"
            "        if isinstance(v, np.ndarray):\n"
            "            if v.size == 0:\n"
            "                return 0.0\n"
            "            flat = np.ravel(v)\n"
            "            pick = target if target < flat.size else 0\n"
            "            v = flat[pick]\n"
            "            target = 0\n"
            "            continue\n"
            "        if isinstance(v, (list, tuple)):\n"
            "            if not v:\n"
            "                return 0.0\n"
            "            pick = target if target < len(v) else 0\n"
            "            v = v[pick]\n"
            "            target = 0\n"
            "            continue\n"
            "        break\n"
            "    # Final hard cast to scalar float for Register(dtype=float64).\n"
            "    arr = np.asarray(v)\n"
            "    if arr.size == 0:\n"
            "        return 0.0\n"
            "    elem = arr.reshape(-1)[0]\n"
            "    try:\n"
            "        return float(elem)\n"
            "    except Exception:\n"
            "        try:\n"
            "            return float(np.real(elem))\n"
            "        except Exception:\n"
            "            return 0.0\n"
        )
        code_context = (scalar_helper + "\n" + code_context).strip()
        
    if "Register._pv_patched" not in code_context:
        monkey_patch = (
            "\n# --- START MONKEY PATCH REGISTER --- \n"
            "# Resolves ValueError: setting an array element with a sequence for PathView engine.\n"
            "try:\n"
            "    from pathsim.utils.register import Register\n"
            "    import numpy as np\n"
            "    if not hasattr(Register, '_pv_patched'):\n"
            "        _orig_setitem = Register.__setitem__\n"
            "        def _pv_safe_setitem(self, key, value):\n"
            "            if isinstance(value, (list, tuple)) and len(value) == 1:\n"
            "                value = value[0]\n"
            "            if isinstance(value, np.ndarray) and getattr(value, 'size', 0) == 1:\n"
            "                value = float(np.real(value.item()))\n"
            "            _orig_setitem(self, key, value)\n"
            "        Register.__setitem__ = _pv_safe_setitem\n"
            "        \n"
            "        _orig_update = Register.update_from_array\n"
            "        def _pv_safe_update(self, arr):\n"
            "            if isinstance(arr, (list, tuple)):\n"
            "                arr = [float(np.real(x.item())) if isinstance(x, np.ndarray) and getattr(x, 'size', 0) == 1 else x for x in arr]\n"
            "            _orig_update(self, arr)\n"
            "        Register.update_from_array = _pv_safe_update\n"
            "        Register._pv_patched = True\n"
            "except Exception:\n"
            "    pass\n"
            "# --- END MONKEY PATCH REGISTER --- \n"
            "\n"
            "# --- START MONKEY PATCH BLOCK CALL ---\n"
            "# Some PathSim versions call block(t) instead of block.update(t).\n"
            "# Block.__call__(self) only accepts self, so redirect to update.\n"
            "try:\n"
            "    from pathsim.blocks._block import Block as _Block\n"
            "    if not hasattr(_Block, '_pv_call_patched'):\n"
            "        _orig_block_call = _Block.__call__\n"
            "        def _pv_safe_block_call(self, *args, **kwargs):\n"
            "            if args or kwargs:\n"
            "                return self.update(*args, **kwargs)\n"
            "            return _orig_block_call(self)\n"
            "        _Block.__call__ = _pv_safe_block_call\n"
            "        _Block._pv_call_patched = True\n"
            "except Exception:\n"
            "    pass\n"
            "# --- END MONKEY PATCH BLOCK CALL ---\n"
        )
        code_context = (monkey_patch + "\n" + code_context).strip()

    duration_expr = duration_override
    if duration_expr is None:
        duration_expr = detect_duration_expr(source_text, sim_var_name) or "10"

    duration_setting = resolve_expr_to_setting(duration_expr, module)
    dt_setting = resolve_expr_to_setting(sim_ctor_kw.get("dt", getattr(sim, "dt", 0.01)), module)

    solver_name = sim_ctor_kw.get("Solver")
    if not solver_name:
        solver_name = getattr(sim.Solver, "__name__", str(sim.Solver))
    engine = getattr(sim, "engine", None)

    adaptive = bool(getattr(engine, "is_adaptive", False))
    atol = getattr(engine, "tolerance_lte_abs", 1e-6)
    rtol = getattr(engine, "tolerance_lte_rel", 1e-3)

    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    pvm = {
        "version": "1.0.0",
        "metadata": {
            "created": now,
            "modified": now,
            "name": model_name,
        },
        "graph": {
            "nodes": pvm_nodes,
            "connections": pvm_connections,
            "annotations": [],
        },
        "events": pvm_events,
        "codeContext": {
            "code": code_context,
        },
        "simulationSettings": {
            "duration": duration_setting,
            "dt": dt_setting,
            "solver": str(solver_name),
            "adaptive": adaptive,
            "atol": str(atol),
            "rtol": str(rtol),
            "ftol": str(sim_ctor_kw.get("tolerance_fpi", getattr(sim, "tolerance_fpi", 1e-12))),
            "dt_min": str(sim_ctor_kw.get("dt_min", getattr(sim, "dt_min", ""))) if sim_ctor_kw.get("dt_min", getattr(sim, "dt_min", None)) is not None else "",
            "dt_max": str(sim_ctor_kw.get("dt_max", getattr(sim, "dt_max", ""))) if sim_ctor_kw.get("dt_max", getattr(sim, "dt_max", None)) is not None else "",
            "ghostTraces": 0,
            "plotResults": True,
        },
    }

    return pvm


def main() -> int:
    args = parse_args()

    input_file = args.input.resolve()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    batch_mode = args.batch or input_file.is_dir()
    input_files = iter_input_files(input_file, args.recursive)

    if not input_files:
        raise FileNotFoundError(f"No Python files found in: {input_file}")

    if not batch_mode and len(input_files) != 1:
        raise ValueError("Multiple input files found but batch mode is disabled")

    successes: List[Path] = []
    skipped: List[Tuple[Path, str]] = []
    failed: List[Tuple[Path, str]] = []

    for src in input_files:
        dst = resolve_output_path(src, input_file if input_file.is_dir() else src.parent, args.output, batch_mode)
        try:
            written = convert_file(src, dst, args)
            successes.append(written)
            if not args.quiet:
                print(f"Wrote {written}")
        except Exception as exc:
            if args.skip_missing_deps and is_missing_dependency_error(exc):
                skipped.append((src, str(exc)))
                if not args.quiet:
                    print(f"Skipped {src}: {exc}")
                continue

            if batch_mode:
                failed.append((src, str(exc)))
                print(f"Failed {src}: {exc}")
                continue
            raise

    if batch_mode:
        if not args.quiet or failed:
            print(f"Summary: converted={len(successes)} skipped={len(skipped)} failed={len(failed)}")
        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
