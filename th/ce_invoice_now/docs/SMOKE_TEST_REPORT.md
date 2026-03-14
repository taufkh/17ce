# Smoke Test Report

Date: 2026-03-05
Module: `ce_invoice_now`
Scope: static smoke tests (without module installation)

## Executed Checks
1. Python bytecode compile (`compileall`) for all module Python files.
2. XML well-formed parsing for all XML files.
3. Manifest sanity:
   - data file references exist
   - CE-only dependency policy (no `account_edi` / `account_edi_ubl_cii`)
4. Access CSV sanity:
   - model id references mapped to module model `_name` values

## Commands Used
```bash
python3 -m compileall -q addons/th/ce_invoice_now
python3 - <<'PY'
import glob, xml.etree.ElementTree as ET
for f in glob.glob('addons/th/ce_invoice_now/**/*.xml', recursive=True):
    ET.parse(f)
print('xml_parse: OK')
PY
```

```bash
python3 - <<'PY'
import ast, csv, glob, os, re, xml.etree.ElementTree as ET
base='addons/th/ce_invoice_now'
raw=open(os.path.join(base,'__manifest__.py'),encoding='utf-8').read()
manifest=ast.literal_eval(raw[raw.find('{'):raw.rfind('}')+1])
errors=[]
for dep in ['account_edi','account_edi_ubl_cii']:
    if dep in manifest.get('depends',[]):
        errors.append(dep)
for rel in manifest.get('data',[]):
    if not os.path.exists(os.path.join(base, rel)):
        errors.append(rel)
for f in glob.glob(base+'/**/*.xml', recursive=True):
    ET.parse(f)
model_names=[]
for f in glob.glob(base+'/**/*.py', recursive=True):
    txt=open(f,encoding='utf-8').read()
    model_names.extend(re.findall(r"_name\s*=\s*'([^']+)'", txt))
expected={f"model_{m.replace('.', '_')}" for m in model_names}
for row in csv.DictReader(open(os.path.join(base,'security','ir.model.access.csv'),encoding='utf-8')):
    mid=row['model_id:id']
    if mid.startswith('model_') and mid not in expected:
        errors.append(mid)
print('SMOKE RESULT:', 'PASS' if not errors else 'FAIL')
print('ERRORS:', errors)
PY
```

## Result
- `compileall`: PASS
- `xml_parse`: PASS
- manifest/data reference checks: PASS
- CE dependency policy check: PASS
- access CSV model mapping check: PASS

Overall smoke test status: **PASS**

## Limitation
Because installation was explicitly skipped, runtime behavior (ORM/view loading in Odoo server) is not executed in this smoke scope.
