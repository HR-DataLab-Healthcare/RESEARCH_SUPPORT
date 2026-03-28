"""Simulate what PathView frontend's hM+Ih functions generate."""
import json, sys, os

pvm_path = os.path.join(os.path.dirname(__file__), 'pathsim-master', 'examples', 'example_cascade.pvm')
d = json.load(open(pvm_path))
cc = d['codeContext']['code']
nodes = d['graph']['nodes']
conns = d['graph']['connections']
settings = d.get('settings', {})
top_events = d['graph'].get('events', [])

o = []

# IMPORTS (matches hM in frontend)
o.append('# IMPORTS')
o.append('import numpy as np')

has_sub = any(n['type'] == 'Subsystem' for n in nodes)
if has_sub:
    o.append('from pathsim import Simulation, Connection, Subsystem, Interface')
else:
    o.append('from pathsim import Simulation, Connection')

# Block imports
block_imports = {}
for n in nodes:
    ntype = n['type']
    if ntype == 'Subsystem' and 'graph' in n:
        for cn in n['graph'].get('nodes', []):
            ct = cn['type']
            if ct not in ('Interface', 'Subsystem'):
                block_imports.setdefault('pathsim.blocks', set()).add(ct)
    elif ntype not in ('Subsystem', 'Interface'):
        block_imports.setdefault('pathsim.blocks', set()).add(ntype)

for path, classes in sorted(block_imports.items()):
    cls_list = sorted(classes)
    o.append('from %s import %s' % (path, ', '.join(cls_list)))

solver = settings.get('solver', 'RKCK54')
o.append('from pathsim.solvers import %s' % solver)

# Top-level event imports
if top_events:
    evt_classes = set()
    for e in top_events:
        cls = e['type'].rsplit('.', 1)[-1]
        evt_classes.add(cls)
    o.append('from pathsim.events import %s' % ', '.join(sorted(evt_classes)))

o.append('')

# CODE CONTEXT
if cc.strip():
    o.append('# CODE CONTEXT')
    o.append(cc.strip())
    o.append('')

# BLOCKS
o.append('# BLOCKS')

# Process subsystem nodes first (simulating Ih)
for n in nodes:
    if n['type'] == 'Subsystem' and 'graph' in n:
        sub_nodes = n['graph'].get('nodes', [])
        sub_conns = n['graph'].get('connections', [])
        sub_events = n['graph'].get('events', [])
        prefix = n.get('name', 'sub') + '_'

        for sn in sub_nodes:
            if sn['type'] == 'Interface':
                o.append('%s = Interface()' % (prefix + 'interface'))
        for sn in sub_nodes:
            if sn['type'] not in ('Interface', 'Subsystem'):
                o.append('%s = %s(...)' % (prefix + sn.get('name', 'block'), sn['type']))
        for se in sub_events:
            etype = se['type'].rsplit('.', 1)[-1]
            o.append('%s = %s(...)' % (prefix + se.get('name', 'event'), etype))
        for j, sc in enumerate(sub_conns):
            o.append('%s_conn_%d = Connection(...)' % (n['name'], j))
        o.append('%s = Subsystem(...)' % n['name'])
        o.append('')

# Top-level non-subsystem blocks
for n in nodes:
    if n['type'] not in ('Subsystem', 'Interface'):
        o.append('%s = %s(...)' % (n.get('name', 'block'), n['type']))

# Show full code with line numbers
full_code = '\n'.join(o)
print("=== GENERATED CODE (relevant lines) ===")
for i, line in enumerate(full_code.split('\n'), 1):
    marker = ' <<<' if 'Schedule' in line else ''
    if i <= 10 or (80 <= i <= 120) or marker:
        print('%3d: %s%s' % (i, line, marker))
    
print('\nTotal lines:', len(full_code.split('\n')))
