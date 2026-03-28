"""Test the derivative PVM — simulates frontend code generation + streaming."""
import json, os

pvm_path = os.path.join(os.path.dirname(__file__), "pathsim-master", "examples", "example_derivative.pvm")
d = json.load(open(pvm_path))
cc = d["codeContext"]["code"]
nodes = d["graph"]["nodes"]
conns = d["graph"]["connections"]
settings = d.get("settings", {})

o = []
o.append("import numpy as np")
o.append("from pathsim import Simulation, Connection")

btypes = set()
for n in nodes:
    if n["type"] not in ("Subsystem", "Interface"):
        btypes.add(n["type"])
o.append("from pathsim.blocks import " + ", ".join(sorted(btypes)))

solver = settings.get("solver", "RKCK54")
o.append("from pathsim.solvers import " + solver)
o.append("")

if cc.strip():
    o.append("# CODE CONTEXT")
    o.append(cc.strip())
    o.append("")

o.append("# BLOCKS")
names = []
nmap = {}
for n in nodes:
    vn = n["name"]
    names.append(vn)
    nmap[n["id"]] = vn
    params = n.get("params", {})
    parts = ["%s=%s" % (k, v) for k, v in params.items() if v is not None and v != ""]
    pstr = ", ".join(parts)
    o.append("%s = %s(%s)" % (vn, n["type"], pstr))

o.append("")
o.append("blocks = [%s]" % ", ".join(names))
o.append("")

o.append("# CONNECTIONS")
for j, c in enumerate(conns):
    src = nmap.get(c["sourceNodeId"], "???")
    tgt = nmap.get(c["targetNodeId"], "???")
    o.append("conn_%d = Connection(%s[%d], %s[%d])" % (j, src, c["sourcePortIndex"], tgt, c["targetPortIndex"]))
cnames = ["conn_%d" % j for j in range(len(conns))]
o.append("connections = [%s]" % ", ".join(cnames))
o.append("")

o.append("sim = Simulation(blocks, connections, dt=%s, Solver=%s)" % (settings.get("dt", "0.01"), solver))
o.append("")

# Test streaming
o.append("count = 0")
o.append("for result in sim.run_streaming(duration=2, reset=True, tickrate=10):")
o.append("    count += 1")
o.append('print(f"STREAMING SUCCESS: {count} yields")')
o.append("")

# Test block(t) call to verify the patch works
o.append("from pathsim.blocks._block import Block as _B")
o.append('print("Block has patch:", hasattr(_B, "_pv_call_patched"))')
o.append("try:")
o.append("    blocks[0](0.5)  # Simulate older PathSim calling block(time)")
o.append('    print("block(t) call: OK")')
o.append("except Exception as e:")
o.append('    print("block(t) call FAILED:", e)')

code = "\n".join(o)
print("=" * 60)
print("EXECUTING GENERATED CODE")
print("=" * 60)
exec(code, {})
