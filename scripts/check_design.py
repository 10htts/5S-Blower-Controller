from pathlib import Path
import sys
root=Path(__file__).parents[1]
required=['AGENTS.md','README.md','docs/safety.md','docs/revision-status.md','firmware/src/controller.h','firmware/tests/test_controller.py','calculations/power-stage.md']
missing=[p for p in required if not (root/p).exists()]
if missing: print('Missing:',*missing,sep='\n'); sys.exit(1)
text=(root/'docs/revision-status.md').read_text()
if 'NOT YET APPROVED TO ORDER' not in text: print('Approval guard missing'); sys.exit(1)
print('PASS: repository structure and provisional-status guards')
