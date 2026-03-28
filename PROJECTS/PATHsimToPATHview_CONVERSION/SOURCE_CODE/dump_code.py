import json
code = json.load(open('d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples/example_cascade.pvm'))['codeContext']['code']
lines = code.splitlines()
for i, line in enumerate(lines):
    print(f"{i+1}: {line}")
