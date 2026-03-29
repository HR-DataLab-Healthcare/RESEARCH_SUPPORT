import json, base64, sys

pvm_path = sys.argv[1] if len(sys.argv) > 1 else "pathsim-master/examples/example_steadystate.pvm"

with open(pvm_path, "r") as f:
    pvm = json.load(f)

print("=== NODES ===")
for n in pvm["graph"]["nodes"]:
    nid = n.get("id", "?")
    ntype = n.get("type", n.get("data", {}).get("type", "?"))
    nparams = n.get("params", n.get("data", {}).get("parameters", {}))
    nname = n.get("name", "")
    ninputs = n.get("inputs", [])
    noutputs = n.get("outputs", [])
    print(f"  {nid} ({nname}) type={ntype} inputs={ninputs} outputs={noutputs} params={nparams}")

print("\n=== CONNECTIONS ===")
for e in pvm["graph"].get("connections", pvm["graph"].get("edges", [])):
    src = e.get("source", "?")
    tgt = e.get("target", "?")
    sh = e.get("sourceHandle", "")
    th = e.get("targetHandle", "")
    print(f"  {src}[{sh}] -> {tgt}[{th}]")

print("\n=== SETTINGS (without codeContext) ===")
settings = pvm.get("settings", {})
filtered = {k: v for k, v in settings.items() if k != "codeContext"}
print(json.dumps(filtered, indent=2))

codeCtx = settings.get("codeContext", "")
if codeCtx:
    print("\n=== CODE CONTEXT ===")
    print(base64.b64decode(codeCtx).decode())
else:
    print("\nNO CODE CONTEXT")
