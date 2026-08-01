from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).parents[1]; out=root/'manufacturing/release-revA.zip'
files=[]
for p in [root/'hardware/outputs', root/'manufacturing', root/'firmware']:
    if p.exists(): files += [x for x in p.rglob('*') if x.is_file() and x.name != out.name]
with ZipFile(out,'w',ZIP_DEFLATED) as z:
    z.writestr('MANUFACTURING-STATUS.txt','REFERENCE REVISION ONLY: NOT APPROVED TO ORDER. Run KiCad ERC/DRC and independent review before use.\n')
    for p in files: z.write(p,p.relative_to(root).as_posix())
print(out)
