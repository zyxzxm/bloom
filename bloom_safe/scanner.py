"""BLOOM SAFE: triagem local básica. Não é antivírus nem garantia de segurança."""
from pathlib import Path
import hashlib, json, zipfile

SUSPICIOUS_EXT={".scr",".bat",".cmd",".ps1",".vbs",".js",".msi",".com",".dll",".sys"}
SUSPICIOUS_NAMES={"autorun.inf"}
def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def inspect_package(path):
    p=Path(path); digest=sha256_file(p); findings=[];entries=[]
    try:
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                name=info.filename; ext=Path(name).suffix.lower()
                if Path(name).name.lower() in SUSPICIOUS_NAMES:findings.append({"file":name,"reason":"nome potencialmente arriscado"})
                if ext in SUSPICIOUS_EXT:findings.append({"file":name,"reason":f"extensão executável/script de risco: {ext}"})
                if Path(name).is_absolute() or ".." in Path(name).parts:findings.append({"file":name,"reason":"caminho de extração inseguro"})
                if info.file_size>512*1024*1024:findings.append({"file":name,"reason":"arquivo muito grande"})
                entries.append({"name":name,"size":info.file_size})
            try:json.loads(z.read(next(n for n in z.namelist() if Path(n).name.lower()=="bloom.json")))
            except (StopIteration,KeyError,json.JSONDecodeError):findings.append({"file":"bloom.json","reason":"manifesto ausente ou inválido"})
    except zipfile.BadZipFile:findings.append({"file":p.name,"reason":"pacote não é um ZIP válido"})
    summary="revisão necessária: foram encontrados indicadores de risco" if findings else "nenhum indicador básico encontrado; isto NÃO comprova que o pacote é seguro"
    return {"file":p.name,"sha256":digest,"entries":entries,"findings":findings,"summary":summary,"checked_by":"BLOOM SAFE local basic checks","disclaimer":"A análise estática é limitada. Todo software de terceiros deve ser tratado como potencialmente perigoso. Nenhuma verificação garante segurança."}
def inspect_and_record(path,history_path):
    result=inspect_package(path);history=Path(history_path);history.parent.mkdir(parents=True,exist_ok=True)
    previous=[]
    try:previous=json.loads(history.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError):pass
    previous.append(result);history.write_text(json.dumps(previous,ensure_ascii=False,indent=2),encoding="utf-8");return result
