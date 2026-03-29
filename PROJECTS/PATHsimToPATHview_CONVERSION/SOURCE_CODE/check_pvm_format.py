"""Check how PathView loads a PVM and what keys it expects."""
import json

# Check the JS bundle for PVM loading logic
js_path = r"C:\Users\PROMET02\anaconda3\Lib\site-packages\pathview\static\assets"

import os
for f in os.listdir(js_path):
    if f.endswith('.js'):
        content = open(os.path.join(js_path, f), 'r', errors='ignore').read()
        # Search for codeContext, simulationSettings, settings key patterns
        for term in ['codeContext', 'simulationSettings', 'settings.', 'loadPvm', 'parsePvm', 'importPvm', 'openFile', '.pvm']:
            idx = content.find(term)
            if idx != -1:
                snippet = content[max(0,idx-80):idx+120]
                print(f"[{f}] '{term}' at {idx}: ...{snippet}...")
                print()
