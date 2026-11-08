"""Rotinas de instalação sem dependência de interface gráfica."""
from pathlib import Path, PureWindowsPath
import zipfile

def safe_extract(zip_path:Path,destination:Path):
    destination.mkdir(parents=True,exist_ok=True)
    root=destination.resolve()
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            member=info.filename.replace("\\", "/")
            win_path=PureWindowsPath(info.filename)
            if win_path.is_absolute() or win_path.drive or ".." in member.split("/"):
                raise ValueError("Arquivo compactado contém caminho inseguro")
            target=(destination/member).resolve()
            if target!=root and root not in target.parents:raise ValueError("Arquivo compactado contém caminho inseguro")
            if info.file_size>512*1024*1024:raise ValueError("Arquivo individual excede 512 MB")
        z.extractall(destination)
