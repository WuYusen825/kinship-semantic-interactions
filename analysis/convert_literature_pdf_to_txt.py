"""将literature下全部PDF转换为逐页UTF-8 TXT；稀疏文本页自动OCR，不改写PDF。"""
from pathlib import Path
import argparse,concurrent.futures,subprocess,hashlib,json,re,os,csv,unicodedata
import fitz
from PIL import Image
import io
ROOT=Path(__file__).resolve().parents[1]

def clean(t):
    return unicodedata.normalize('NFKC',''.join(c for c in t if c in '\n\t' or ord(c)>=32))
def nchar(t):return len(re.sub(r'\s','',t))
def ocr_page(task):
    pdf,index,digest,dpi=task
    cache=ROOT/'.cache/pdf_ocr'/digest/f'page_{index+1:04d}.txt'
    if cache.exists():return pdf,index,cache.read_text(),True
    with fitz.open(pdf) as doc:
        pix=doc[index].get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
        png=pix.tobytes('png')
    im=Image.open(io.BytesIO(png)).convert('L');h=im.histogram()
    ink=sum(h[:170])/(im.width*im.height)
    if ink<0.00005:text=''
    else:
        env=dict(os.environ,OMP_THREAD_LIMIT='1')
        r=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','3'],input=png,capture_output=True,env=env)
        if r.returncode:raise RuntimeError(str(pdf)+f' page {index+1}: '+r.stderr.decode('utf8','replace'))
        text=clean(r.stdout.decode('utf8','replace'))
        if nchar(text)<100:
            sparse=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','11'],input=png,capture_output=True,env=env)
            if sparse.returncode==0:
                candidate=clean(sparse.stdout.decode('utf8','replace'))
                if nchar(candidate)>nchar(text):text=candidate
    cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(text)
    return pdf,index,text,False

def save(state):
    p=state['pdf'];pages=state['pages'];methods=state['methods'];parts=[
        '# PDF全文文本（UTF-8）',f"来源PDF：{p.relative_to(ROOT)}",f"原PDF SHA-256：{state['sha']}",
        '页码表示PDF文件页序，不自动等同于期刊印刷页码。Native为原文本层，OCR为扫描或低文字页识别；表格、音标、公式与OCR仍须对照PDF。','']
    for i,t in enumerate(pages):
        parts.append(f'===== PDF PAGE {i+1:04d} / {len(pages):04d} | {methods[i]} =====')
        parts.append(clean(t).rstrip() or '[本页未提取出文字：可能为空白、图像或OCR未识别内容，请对照原PDF。]')
        parts.append('')
    txt=p.with_suffix('.txt');txt.write_text('\n'.join(parts),encoding='utf8')
    return txt

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);ap.add_argument('--dpi',type=int,default=200);a=ap.parse_args()
    files=sorted((ROOT/'literature').rglob('*.pdf'));states={};tasks=[]
    for p in files:
        with fitz.open(p) as doc:n=doc.page_count
        r=subprocess.run(['pdftotext','-layout',str(p),'-'],capture_output=True)
        if r.returncode:raise RuntimeError(str(p)+r.stderr.decode('utf8','replace'))
        pages=r.stdout.decode('utf8','replace').split('\f')
        if len(pages)==n+1 and not pages[-1].strip():pages.pop()
        assert len(pages)==n,(p,len(pages),n)
        sha=hashlib.sha256(p.read_bytes()).hexdigest();methods=['Native']*n
        for i,t in enumerate(pages):
            if nchar(clean(t))<100:methods[i]='OCR_PENDING';tasks.append((p,i,sha,a.dpi))
        states[p]={'pdf':p,'pages':pages,'methods':methods,'sha':sha,'native_char_counts':[nchar(clean(t)) for t in pages]}
        save(states[p])
    print(f'已建立 {len(files)} 份TXT；需OCR {len(tasks)} 页。',flush=True)
    done=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futures=[ex.submit(ocr_page,t) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            p,i,text,cached=f.result();s=states[p];old=clean(s['pages'][i])
            s['pages'][i]=text if nchar(text)>=nchar(old) else old
            s['methods'][i]='OCR' if nchar(text)>=nchar(old) else 'Native_after_OCR_check'
            done+=1
            if done%10==0 or done==len(tasks):print(f'OCR {done}/{len(tasks)} 页完成',flush=True)
    report=[]
    for p,s in states.items():
        txt=save(s);low=[i+1 for i,t in enumerate(s['pages']) if nchar(clean(t))<100]
        report.append({'pdf':str(p.relative_to(ROOT)),'txt':str(txt.relative_to(ROOT)),'pdf_sha256':s['sha'],'txt_sha256':hashlib.sha256(txt.read_bytes()).hexdigest(),'pages':len(s['pages']),'ocr_attempted_pages':sum(m!='Native' for m in s['methods']),'pages_still_low_text':low,'characters':len(txt.read_text()),'page_methods':s['methods'],'quality_note':'OCR、公式、音标与表格转写应对照PDF；低文字页不自动等同于缺页。'})
    result={'pdf_files':len(files),'txt_files':len(report),'total_pdf_pages':sum(x['pages'] for x in report),'ocr_attempted_pages':len(tasks),'dpi':a.dpi,'source_pdfs_unchanged':all(hashlib.sha256((ROOT/x['pdf']).read_bytes()).hexdigest()==x['pdf_sha256'] for x in report),'files':report}
    (ROOT/'literature/pdf_text_conversion_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    with (ROOT/'literature/pdf_text_conversion_report.csv').open('w',encoding='utf-8-sig',newline='') as out:
        w=csv.DictWriter(out,fieldnames=['pdf','txt','pages','ocr_attempted_pages','pages_still_low_text','characters']);w.writeheader()
        for x in report:w.writerow({k:x[k] for k in w.fieldnames})
    lines=['# 全部PDF的TXT索引','','每个PDF都有同目录、同文件名的UTF-8 TXT。每页保留PDF页序标记，扫描及低文本页已尝试OCR。正式文献与早期版本／补充材料分别计数，转换不新增文献数量。','','| PDF | TXT | 页数 | OCR页数 | 低文字页（需对照PDF） |','|---|---|---:|---:|---|']
    for x in report:
        pdf=Path(x['pdf']).relative_to('literature');txt=Path(x['txt']).relative_to('literature');low=x['pages_still_low_text'];label=', '.join(map(str,low[:15]))+(' …' if len(low)>15 else '')
        lines.append(f"| [{pdf}]({pdf.as_posix()}) | [TXT]({txt.as_posix()}) | {x['pages']} | {x['ocr_attempted_pages']} | {label or '—'} |")
    (ROOT/'literature/TXT索引.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
