# py_to_pvm Usage

`py_to_pvm.py` converts PathSim Python models into PathView `.pvm` files.

## Single File

Convert one model:

```powershell
python "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/py_to_pvm.py" `
  "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples/example_feedback.py" `
  -o "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples/example_feedback.pvm" `
  --pathsim-root "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master"
```

If the script contains multiple `Simulation` objects, choose one explicitly:

```powershell
python "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/py_to_pvm.py" `
  "model.py" `
  --sim-var Sim `
  --pathsim-root "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master"
```

## Batch Conversion

Convert every `.py` file in a folder:

```powershell
python "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/py_to_pvm.py" `
  "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples" `
  --batch `
  --pathsim-root "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master"
```

Convert recursively:

```powershell
python "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/py_to_pvm.py" `
  "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples" `
  --batch `
  --recursive `
  --pathsim-root "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master"
```

## Optional Dependency Handling

Skip files that fail only because an optional import is missing:

```powershell
python "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/py_to_pvm.py" `
  "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples" `
  --batch `
  --skip-missing-deps `
  --pathsim-root "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master"
```

## Quiet Mode

Suppress progress output and output from imported model scripts:

```powershell
python "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/py_to_pvm.py" `
  "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples" `
  --batch `
  --quiet `
  --pathsim-root "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master"
```

## Useful Flags

- `--code-context auto|full|none`
- `--duration 5`
- `--name my-model`
- `--sim-var Sim`
- `--quiet`
- `--skip-missing-deps`

## Notes

- The converter executes the input Python file to discover the `Simulation` object.
- Use `--quiet` if the imported model produces a lot of logging.
- `--skip-missing-deps` only skips import-related failures; real conversion errors still fail.

## Next Steps

After generating `.pvm` files, a practical workflow is:

1. Open the `.pvm` in PathView and confirm the graph loads without code errors.
2. Run the model once in PathView to verify that `codeContext`, events, and block parameters execute correctly.
3. Compare the PathView simulation output against the original Python model for one or two representative cases.
4. If a converted model is too noisy or too literal, rerun conversion with a different `--code-context` mode.
5. For large folders, use `--batch --quiet` first, then inspect only the models that need manual cleanup.
6. If a file depends on optional packages, install those packages or use `--skip-missing-deps` during batch runs.

Recommended validation commands:

```powershell
Get-ChildItem "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples" -Filter *.pvm
```

```powershell
python "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/py_to_pvm.py" `
  "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master/examples" `
  --batch `
  --quiet `
  --pathsim-root "d:/OneDrive - Hogeschool Rotterdam/AA_CODE/PATHSIM+PATHVIEW/pathsim-master"
```