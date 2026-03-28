"""Simulate PathView frontend's Ih() code generation from PVM graph."""
import json
import sys

sys.path.insert(0, "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/src")

pvm = json.load(open("d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples/example_cascade.pvm"))

plant_node = [n for n in pvm["graph"]["nodes"] if n["name"] == "plant"][0]
g = plant_node["graph"]

code_lines = []
internal_vars = []
id_to_var = {}

for child in g["nodes"]:
    if child["type"] == "Interface":
        var = "plant_interface"
        code_lines.append(f"{var} = Interface()")
    else:
        var = "plant_" + child["name"]
        params_parts = []
        for k, v in child.get("params", {}).items():
            if v is not None and v != "":
                params_parts.append(f"{k}={v}")
        param_str = ", ".join(params_parts)
        code_lines.append(f"{var} = {child['type']}({param_str})")
    internal_vars.append(var)
    id_to_var[child["id"]] = var

conn_vars = []
for i, c in enumerate(g["connections"]):
    src = id_to_var[c["sourceNodeId"]]
    tgt = id_to_var[c["targetNodeId"]]
    cv = f"plant_conn_{i}"
    code_lines.append(f"{cv} = Connection({src}[{c['sourcePortIndex']}], {tgt}[{c['targetPortIndex']}])")
    conn_vars.append(cv)

blocks_str = ", ".join(internal_vars)
conns_str = ", ".join(conn_vars)
code_lines.append(f"plant = Subsystem(blocks=[{blocks_str}], connections=[{conns_str}])")

full_code = "\n".join(code_lines)
print("Generated code:")
print(full_code)
print()

ns = {}
exec(pvm["codeContext"]["code"], ns)
exec(full_code, ns)
print("SUCCESS! plant =", ns["plant"])
print("plant.blocks:", [type(b).__name__ for b in ns["plant"].blocks])
print("plant.interface:", type(ns["plant"].interface).__name__)
