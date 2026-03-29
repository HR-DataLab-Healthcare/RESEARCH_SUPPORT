import json
pvm = json.load(open('pathsim-master/examples/example_steadystate.pvm'))
for c in pvm['graph']['connections']:
    print(f"  {c['sourceNodeId']}[{c['sourcePortIndex']}] -> {c['targetNodeId']}[{c['targetPortIndex']}]")
print()
print("TOP LEVEL KEYS:", list(pvm.keys()))
print("SETTINGS:", pvm.get('settings', {}))
print("SIMULATION:", pvm.get('simulation', {}))
# Check all top-level keys for anything simulation-related
for k in pvm.keys():
    if k != 'graph':
        print(f"{k}: {json.dumps(pvm[k])[:200]}")
