"""Search PathView JS for PVM loading/parsing logic."""
import os, re

js_path = r"C:\Users\PROMET02\anaconda3\Lib\site-packages\pathview\static\app\immutable\chunks"

for f in sorted(os.listdir(js_path)):
    if not f.endswith('.js'):
        continue
    content = open(os.path.join(js_path, f), 'r', errors='ignore').read()
    for term in ['codeContext', 'simulationSettings', 'loadProject', 'parseProject', '.pvm', 'importProject', 'fileContent', 'JSON.parse']:
        idx = 0
        while True:
            idx = content.find(term, idx)
            if idx == -1:
                break
            snippet = content[max(0,idx-100):idx+150].replace('\n',' ')
            print(f"[{f}] '{term}' at {idx}: ...{snippet}...")
            print()
            idx += len(term)
