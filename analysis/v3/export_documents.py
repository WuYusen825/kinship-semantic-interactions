"""Export the independent Chinese third version with the user-supplied font profile."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[2]

def main():
    source=ROOT/'outputs/论文_中文第三版.md'
    if not source.exists():raise SystemExit('第三版正文尚未完成，不能导出。')
    subprocess.run([sys.executable,'analysis/export_forum_documents.py','--input',str(source),
       '--name','论文_中文第三版','--abstract-name','第三版_摘要','--page-numbers',
       '--format-profile','notes/format/中文模板_格式规则.json'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'analysis/audit_revision_artifacts.py','--input',str(source),
       '--name','论文_中文第三版','--abstract-name','第三版_摘要','--output','notes/v3/artifact_check.json',
       '--body-han-min','10000','--body-han-max','15000','--discussion-min-share','0.45'],cwd=ROOT,check=True)
    print('第三版MD/Word/PDF/TXT及摘要已导出并核对。Word指定模板字体；PDF使用已登记替代字体预览。')

if __name__=='__main__':main()
