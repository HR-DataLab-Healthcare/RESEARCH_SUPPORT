"""
Full end-to-end test: simulate exactly what PathView's frontend JS (hM + Ih)
generates from our PVM and then exec it to prove it works.
"""
import json, sys, os, re

pvm_path = os.path.join(
    os.path.dirname(__file__),
    "pathsim-master", "examples", "example_cascade.pvm"
)
d = json.load(open(pvm_path))
cc = d["codeContext"]["code"]
nodes = d["graph"]["nodes"]
conns = d["graph"]["connections"]
settings = d.get("settings", {})
top_events = d["graph"].get("events", [])

# ─── Reproduce the frontend JS hM() function faithfully ───

o = []

# === IMPORTS (hM lines) ===
o.append("# IMPORTS")
o.append("import numpy as np")

has_sub = any(n["type"] == "Subsystem" for n in nodes)
if has_sub:
    o.append("from pathsim import Simulation, Connection, Subsystem, Interface")
else:
    o.append("from pathsim import Simulation, Connection")

# u_ function: collect block type imports from all nodes (including subsystem children)
block_imports = {}
def collect_imports(node_list):
    for n in node_list:
        ntype = n["type"]
        if ntype == "Subsystem" and "graph" in n:
            collect_imports(n["graph"].get("nodes", []))
        elif ntype not in ("Subsystem", "Interface"):
            # In the real frontend, Es.get(type) gives the blockClass and module
            block_imports.setdefault("pathsim.blocks", set()).add(ntype)

collect_imports(nodes)
for path, classes in sorted(block_imports.items()):
    o.append("from %s import %s" % (path, ", ".join(sorted(classes))))

solver = settings.get("solver", "RKCK54")
o.append("from pathsim.solvers import %s" % solver)

# Top-level event imports: c&&o.push(`from pathsim.events import ${[...u].join(", ")}`)
# Only if there are top-level events
if top_events:
    evt_classes = set()
    for e in top_events:
        cls = e["type"].rsplit(".", 1)[-1]
        evt_classes.add(cls)
    o.append("from pathsim.events import %s" % ", ".join(sorted(evt_classes)))

o.append("")

# === CODE CONTEXT ===
if cc.strip():
    o.append("# CODE CONTEXT")
    o.append(cc.strip())
    o.append("")

# === BLOCKS (Ih for subsystems, then top-level) ===
o.append("# BLOCKS")

node_vars = {}    # id -> varname
all_names = []

def gen_subsystem(node, prefix=""):
    """Reproduce JS Ih() function"""
    sub_nodes = node["graph"].get("nodes", [])
    sub_conns = node["graph"].get("connections", [])
    sub_events = node["graph"].get("events", [])
    name = node.get("name", "subsystem_%d" % len(all_names))
    all_names.append(name)
    node_vars[node["id"]] = name
    pfx = prefix + name + "_"

    block_names = []
    id_map = {}

    # Interface nodes
    for sn in sub_nodes:
        if sn["type"] == "Interface":
            vn = pfx + "interface"
            block_names.append(vn)
            id_map[sn["id"]] = vn
            o.append("%s = Interface()" % vn)

    # Regular blocks
    for sn in sub_nodes:
        if sn["type"] not in ("Interface", "Subsystem"):
            vn = pfx + sn.get("name", "block_%d" % len(block_names))
            block_names.append(vn)
            id_map[sn["id"]] = vn
            params = sn.get("params", {})
            pstr = ", ".join("%s=%s" % (k, v) for k, v in params.items() if v != "" and v is not None)
            o.append("%s = %s(%s)" % (vn, sn["type"], pstr))

    # Propagate id_map back
    for sid, svn in id_map.items():
        node_vars[sid] = svn

    # Events
    evt_names = []
    for se in sub_events:
        etype = se["type"].rsplit(".", 1)[-1]
        vn = pfx + se.get("name", "event_%d" % len(evt_names))
        evt_names.append(vn)
        params = se.get("params", {})
        pstr = ", ".join("%s=%s" % (k, v) for k, v in params.items() if v != "" and v is not None)
        o.append("%s = %s(%s)" % (vn, etype, pstr))

    # Connections
    conn_names = []
    for j, sc in enumerate(sub_conns):
        cn = "%s_conn_%d" % (name, j)
        conn_names.append(cn)
        src_var = id_map.get(sc["sourceNodeId"], "???")
        tgt_var = id_map.get(sc["targetNodeId"], "???")
        o.append("%s = Connection(%s[%d], %s[%d])" % (
            cn, src_var, sc["sourcePortIndex"], tgt_var, sc["targetPortIndex"]))

    # Subsystem constructor
    blocks_str = ", ".join(block_names)
    conns_str = ", ".join(conn_names)
    if evt_names:
        evts_str = ", ".join(evt_names)
        o.append("%s = Subsystem(" % name)
        o.append("    blocks=[%s]," % blocks_str)
        o.append("    connections=[%s]," % conns_str)
        o.append("    events=[%s]," % evts_str)
        o.append(")")
    else:
        o.append("%s = Subsystem(blocks=[%s], connections=[%s])" % (name, blocks_str, conns_str))
    o.append("")

# Generate subsystem nodes first
for n in nodes:
    if n["type"] == "Subsystem" and "graph" in n:
        gen_subsystem(n)

# Top-level non-subsystem blocks
for n in nodes:
    if n["type"] not in ("Subsystem", "Interface"):
        vn = n.get("name", "block_%d" % len(all_names))
        all_names.append(vn)
        node_vars[n["id"]] = vn
        params = n.get("params", {})
        pstr = ", ".join("%s=%s" % (k, v) for k, v in params.items() if v != "" and v is not None)
        o.append("%s = %s(%s)" % (vn, n["type"], pstr))

o.append("")
o.append("blocks = [%s]" % ", ".join(all_names))
o.append("")

# Connections
o.append("# CONNECTIONS")
conn_names = []
for j, c in enumerate(conns):
    cn = "conn_%d" % j
    conn_names.append(cn)
    src = node_vars.get(c["sourceNodeId"], "???")
    tgt = node_vars.get(c["targetNodeId"], "???")
    o.append("%s = Connection(%s[%d], %s[%d])" % (
        cn, src, c["sourcePortIndex"], tgt, c["targetPortIndex"]))
o.append("connections = [%s]" % ", ".join(conn_names))
o.append("")

# Simulation (but don't run it)
o.append("# SIMULATION")
o.append("sim = Simulation(blocks, connections, dt=%s, Solver=%s)" % (
    settings.get("dt", 0.01), solver))
o.append("")
o.append("print('SUCCESS! Simulation created:', sim)")

# ─── Join and show critical lines ───
full_code = "\n".join(o)
lines = full_code.split("\n")
print("=" * 60)
print("GENERATED CODE (%d lines)" % len(lines))
print("=" * 60)
for i, line in enumerate(lines, 1):
    marker = ""
    if "Schedule" in line:
        marker = "  <<<< SCHEDULE"
    if i <= 10 or (75 <= i <= 115) or marker:
        print("%3d: %s%s" % (i, line, marker))
    elif i == 11:
        print("     ... (monkey patch + helper) ...")

print()
print("=" * 60)
print("EXECUTING GENERATED CODE...")
print("=" * 60)

try:
    exec(full_code, {})
    print("\nSUCCESS!")
except Exception as e:
    print("\nFAILED: %s" % e)
    import traceback
    traceback.print_exc()
