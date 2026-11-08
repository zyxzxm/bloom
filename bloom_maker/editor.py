"""BLOOM MAKER 2D: editor visual de cenas, blocos por eventos e mídia importada."""
import json
import shutil
import tkinter as tk
import uuid
import zipfile
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog

from PIL import Image, ImageTk

DEFAULT = {
    "maker_version": 2,
    "project": {"name": "Meu jogo", "version": "1.0.0", "format": "bloom"},
    "scene": {"name": "Cena 1", "width": 960, "height": 540, "background": "#e7fcff", "objects": []},
}
BLOCKS = {
    "Mover para a direita": ("move_x", 20),
    "Mover para a esquerda": ("move_x", -20),
    "Mover para baixo": ("move_y", 20),
    "Mover para cima": ("move_y", -20),
    "Mostrar texto": ("say", "Olá!"),
    "Trocar cor": ("set_color", "#20a99e"),
    "Reproduzir música/áudio": ("play_sound", ""),
}

class Maker(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("BLOOM MAKER — engine 2D visual")
        self.geometry("1240x780")
        self.minsize(1000, 650)
        self.configure(bg="#eef4f7")
        self.doc = json.loads(json.dumps(DEFAULT))
        self.path = None
        self.asset_dir = Path.home() / ".bloom-maker-assets" / uuid.uuid4().hex
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        self._images = []
        self._preview_images = []
        self._audio_playing = False
        self._build()
        self.refresh()

    def _build(self):
        bar = tk.Frame(self, bg="#123b46")
        bar.pack(fill="x")
        tk.Label(bar, text="BLOOM MAKER 2D", bg="#123b46", fg="white", font=("Segoe UI", 15, "bold")).pack(side="left", padx=16, pady=10)
        for label, command in [("Novo objeto", self.add_object), ("Importar imagem", self.import_image), ("Importar áudio", self.import_audio), ("Excluir objeto", self.delete_object), ("Abrir", self.open_file), ("Salvar projeto", self.save_file), ("Exportar ZIP", self.export_package), ("Prévia", self.preview)]:
            ttk.Button(bar, text=label, command=command).pack(side="left", padx=4, pady=8)
        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=10)
        left = ttk.Frame(body, padding=8)
        center = ttk.Frame(body, padding=8)
        right = ttk.Frame(body, padding=8)
        body.add(left, weight=1); body.add(center, weight=4); body.add(right, weight=2)
        ttk.Label(left, text="OBJETOS", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.objects = ttk.Treeview(left, columns=("type",), show="tree headings", height=18)
        self.objects.heading("#0", text="Cena"); self.objects.heading("type", text="Tipo")
        self.objects.pack(fill="both", expand=True, pady=(6, 8)); self.objects.bind("<<TreeviewSelect>>", self.select_object)
        ttk.Label(left, text="Uma cena 2D. Arraste objetos no canvas.", wraplength=170).pack(anchor="w")
        self.canvas = tk.Canvas(center, bg="#ffffff", highlightbackground="#b9d0d7", highlightthickness=1, width=720, height=440)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click); self.canvas.bind("<B1-Motion>", self.canvas_drag); self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        form = ttk.LabelFrame(center, text="Propriedades do objeto", padding=7); form.pack(fill="x", pady=(8, 0))
        self.vars = {}
        for i, (label, key) in enumerate([("Nome", "name"), ("X", "x"), ("Y", "y"), ("Largura", "width"), ("Altura", "height"), ("Cor", "color")]):
            row, col = divmod(i, 3)
            ttk.Label(form, text=label).grid(row=row * 2, column=col, sticky="w", padx=5)
            var = tk.StringVar(); self.vars[key] = var
            ttk.Entry(form, textvariable=var, width=16).grid(row=row * 2 + 1, column=col, sticky="ew", padx=5, pady=(0, 5))
            form.columnconfigure(col, weight=1)
        ttk.Button(form, text="Escolher cor", command=self.pick_color).grid(row=0, column=3, rowspan=2, padx=5)
        ttk.Button(form, text="Aplicar", command=self.apply_properties).grid(row=2, column=3, rowspan=2, padx=5)
        ttk.Label(right, text="BLOCOS DE CÓDIGO", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(right, text="Escolha um bloco e quando ele executa.", wraplength=240).pack(anchor="w", pady=(3, 8))
        self.trigger_var = tk.StringVar(value="Ao iniciar")
        ttk.Combobox(right, textvariable=self.trigger_var, values=["Ao iniciar", "Ao clicar"], state="readonly").pack(fill="x", pady=3)
        self.block_var = tk.StringVar(value=next(iter(BLOCKS)))
        ttk.Combobox(right, textvariable=self.block_var, values=list(BLOCKS), state="readonly").pack(fill="x", pady=3)
        self.block_value = tk.StringVar()
        ttk.Entry(right, textvariable=self.block_value).pack(fill="x", pady=3)
        ttk.Button(right, text="Adicionar bloco", command=self.add_block).pack(fill="x", pady=(3, 8))
        self.block_list = tk.Listbox(right, height=14, font=("Segoe UI", 10), activestyle="none", selectbackground="#d7f1ed")
        self.block_list.pack(fill="both", expand=True)
        ttk.Button(right, text="Remover bloco selecionado", command=self.delete_block).pack(fill="x", pady=6)
        ttk.Label(right, text="Exemplos: iniciar → mover; clicar → dizer texto; iniciar → tocar áudio.", wraplength=240).pack(anchor="w", pady=8)

    def selected(self):
        selection = self.objects.selection()
        if not selection: return None
        try: return self.doc["scene"]["objects"][int(selection[0])]
        except (ValueError, IndexError): return None

    def add_object(self):
        n = len(self.doc["scene"]["objects"]) + 1
        obj = {"name": f"Objeto {n}", "type": "rect", "x": 80 + n * 16, "y": 70 + n * 12, "width": 120, "height": 80, "color": "#20a99e", "blocks": []}
        self.doc["scene"]["objects"].append(obj); self.refresh(); self.objects.selection_set(str(n - 1)); self.select_object()

    def delete_object(self):
        selection = self.objects.selection()
        if selection:
            self.doc["scene"]["objects"].pop(int(selection[0])); self.refresh()

    def refresh(self):
        self.objects.delete(*self.objects.get_children())
        for i, obj in enumerate(self.doc["scene"]["objects"]):
            self.objects.insert("", "end", iid=str(i), text=obj.get("name", f"Objeto {i+1}"), values=(obj.get("type", "rect"),))
        self.draw_scene(); self.refresh_blocks()

    def select_object(self, event=None):
        obj = self.selected()
        if obj:
            for key, var in self.vars.items(): var.set(str(obj.get(key, "")))
            self.refresh_blocks()

    def apply_properties(self, event=None):
        obj = self.selected()
        if not obj: return
        try:
            obj["name"] = self.vars["name"].get()[:80]
            for key in ("x", "y", "width", "height"): obj[key] = max(0, min(10000, int(self.vars[key].get())))
            color = self.vars["color"].get()
            if not color.startswith("#") or len(color) not in (4, 7): raise ValueError("Cor inválida")
            obj["color"] = color
            self.refresh(); self.objects.selection_set(str(self.doc["scene"]["objects"].index(obj)))
        except ValueError as exc: messagebox.showerror("Propriedade inválida", f"Confira posição, tamanho e cor. {exc}", parent=self)

    def pick_color(self):
        chosen = colorchooser.askcolor(color=self.vars["color"].get() or "#20a99e", parent=self)
        if chosen[1]: self.vars["color"].set(chosen[1]); self.apply_properties()

    def _media_path(self, relative):
        if not relative: return None
        value = Path(relative)
        if value.is_absolute() and value.exists(): return value
        roots = [self.asset_dir]
        if self.path: roots.append(self.path.with_name(self.path.name + "_assets"))
        for root in roots:
            candidate = root / value.name
            if candidate.is_file(): return candidate
        return None

    def import_image(self):
        obj = self.selected()
        if not obj: self.add_object(); obj = self.selected()
        path = filedialog.askopenfilename(parent=self, filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.gif")])
        if not path: return
        try:
            Image.open(path).verify()
        except Exception as exc: messagebox.showerror("Imagem inválida", str(exc), parent=self); return
        src = Path(path); dest = self.asset_dir / (uuid.uuid4().hex + src.suffix.lower()); shutil.copy2(src, dest)
        obj["type"] = "image"; obj["image"] = dest.name
        self.refresh(); self.objects.selection_set(str(self.doc["scene"]["objects"].index(obj))); self.select_object()

    def import_audio(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("Áudio", "*.wav *.ogg *.mp3")])
        if not path: return
        src = Path(path); dest = self.asset_dir / (uuid.uuid4().hex + src.suffix.lower()); shutil.copy2(src, dest)
        self.doc.setdefault("assets", []).append({"type": "audio", "path": dest.name})
        messagebox.showinfo("Áudio importado", f"Áudio adicionado ao projeto: {src.name}\nAdicione um bloco ‘Reproduzir música/áudio’ e informe {dest.name} no campo de valor.", parent=self)

    def add_block(self):
        obj = self.selected()
        if not obj: messagebox.showinfo("Blocos", "Selecione um objeto primeiro.", parent=self); return
        label = self.block_var.get(); action, default = BLOCKS[label]; value = self.block_value.get().strip() or str(default)
        if action == "play_sound" and value == "":
            audio = next((a["path"] for a in self.doc.get("assets", []) if a.get("type") == "audio"), "")
            value = audio
        trigger = "start" if self.trigger_var.get() == "Ao iniciar" else "click"
        obj.setdefault("blocks", []).append({"trigger": trigger, "action": action, "value": value})
        self.refresh_blocks()

    def refresh_blocks(self):
        if not hasattr(self, "block_list"): return
        self.block_list.delete(0, "end"); obj = self.selected()
        if not obj: return
        labels = {"move_x":"mover X", "move_y":"mover Y", "say":"mostrar texto", "set_color":"trocar cor", "play_sound":"tocar áudio"}
        for block in obj.get("blocks", []):
            when = "Ao iniciar" if block.get("trigger") == "start" else "Ao clicar"
            self.block_list.insert("end", f'{when}  →  {labels.get(block.get("action"), block.get("action"))}: {block.get("value", "")}')

    def delete_block(self):
        obj = self.selected(); selection = self.block_list.curselection()
        if obj and selection:
            obj.get("blocks", []).pop(selection[0]); self.refresh_blocks()

    def draw_scene(self):
        self.canvas.delete("all"); self._images = []
        self.canvas.create_rectangle(0, 0, 960, 540, fill=self.doc["scene"].get("background", "#e7fcff"), outline="")
        for i, obj in enumerate(self.doc["scene"]["objects"]): self._draw_object(self.canvas, obj, i, self._images)

    def _draw_object(self, canvas, obj, index, image_refs):
        x, y, w, h = (int(obj.get(key, 0)) for key in ("x", "y", "width", "height")); tag = str(index)
        if obj.get("type") == "image":
            media = self._media_path(obj.get("image"))
            if media:
                try:
                    image = Image.open(media).convert("RGBA"); image.thumbnail((max(1,w), max(1,h))); photo = ImageTk.PhotoImage(image); image_refs.append(photo); canvas.create_image(x, y, image=photo, anchor="nw", tags=(tag,)); return
                except Exception: pass
            canvas.create_rectangle(x,y,x+w,y+h,fill="#e8c7cf",outline="#a04458",tags=(tag,)); label="Imagem ausente"
        else:
            fill=obj.get("color", "#20a99e")
            if obj.get("type")=="ellipse": canvas.create_oval(x,y,x+w,y+h,fill=fill,outline="#ffffff",width=2,tags=(tag,))
            else: canvas.create_rectangle(x,y,x+w,y+h,fill=fill,outline="#ffffff",width=2,tags=(tag,))
            label=obj.get("text") or obj.get("name", "Objeto")
        canvas.create_text(x+w/2,y+h/2,text=label,fill="#173b46",tags=(tag,))

    def canvas_click(self, event):
        item=self.canvas.find_withtag("current")
        if item:
            tags=self.canvas.gettags(item[0])
            if tags and tags[0].isdigit():
                self.drag_index=int(tags[0]);self.drag_start=(event.x,event.y);self.objects.selection_set(tags[0]);self.select_object()

    def canvas_drag(self, event):
        if not hasattr(self,"drag_index") or not hasattr(self,"drag_start"):return
        obj=self.doc["scene"]["objects"][self.drag_index];dx=event.x-self.drag_start[0];dy=event.y-self.drag_start[1];obj["x"]=max(0,int(obj.get("x",0)+dx));obj["y"]=max(0,int(obj.get("y",0)+dy));self.drag_start=(event.x,event.y);self.draw_scene()

    def canvas_release(self, event):
        if hasattr(self,"drag_start"):del self.drag_start
        if hasattr(self,"drag_index"):del self.drag_index
        obj=self.selected()
        if obj:
            for key in ("x","y"):self.vars[key].set(str(obj[key]))

    def open_file(self):
        filename=filedialog.askopenfilename(filetypes=[("Projeto BLOOM", "*.bloom.json"),("JSON", "*.json")],parent=self)
        if not filename:return
        try:
            doc=json.loads(Path(filename).read_text(encoding="utf-8"));self.validate(doc);self.doc=doc;self.path=Path(filename);self.refresh()
        except Exception as exc:messagebox.showerror("Não foi possível abrir",str(exc),parent=self)

    def validate(self, doc):
        if not isinstance(doc.get("scene",{}).get("objects"),list):raise ValueError("Arquivo sem lista scene.objects")
        if len(doc["scene"]["objects"])>1000:raise ValueError("Limite de 1000 objetos por cena")
        for obj in doc["scene"]["objects"]:
            for key in ("x","y","width","height"):int(obj[key])
            if obj.get("type") not in {"rect","ellipse","image","text"}:raise ValueError("Tipo de objeto desconhecido")
            for block in obj.get("blocks",[]):
                if block.get("action") not in {"move_x","move_y","say","set_color","play_sound"}:raise ValueError("Ação de bloco desconhecida")

    def _copy_assets_for_save(self, target):
        folder=target.with_name(target.name+"_assets");folder.mkdir(parents=True,exist_ok=True)
        for obj in self.doc["scene"]["objects"]:
            if obj.get("image"):
                source=self._media_path(obj["image"])
                if source:
                    dest=folder/source.name
                    if source.resolve()!=dest.resolve():shutil.copy2(source,dest)
                    obj["image"]=source.name
        for asset in self.doc.get("assets",[]):
            if asset.get("type")=="audio":
                source=self._media_path(asset.get("path"))
                if source:
                    dest=folder/source.name
                    if source.resolve()!=dest.resolve():shutil.copy2(source,dest)
                    asset["path"]=source.name
        for obj in self.doc["scene"]["objects"]:
            for block in obj.get("blocks",[]):
                if block.get("action")=="play_sound":
                    source=self._media_path(str(block.get("value","")))
                    if source:
                        dest=folder/source.name
                        if source.resolve()!=dest.resolve():shutil.copy2(source,dest)
                        block["value"]=source.name
        self.asset_dir=folder

    def save_file(self):
        if self.path:
            target=self.path
        else:
            chosen=filedialog.asksaveasfilename(defaultextension=".bloom.json",filetypes=[("Projeto BLOOM","*.bloom.json")],parent=self)
            if not chosen:return
            target=Path(chosen)
        self.path=target;self._copy_assets_for_save(target);target.write_text(json.dumps(self.doc,ensure_ascii=False,indent=2),encoding="utf-8");messagebox.showinfo("BLOOM MAKER","Projeto e mídia salvos. Para compartilhar, compacte o arquivo .bloom.json junto da pasta .bloom.json_assets.",parent=self)

    def export_package(self):
        destination=filedialog.asksaveasfilename(parent=self,defaultextension=".zip",filetypes=[("Pacote BLOOM","*.zip")])
        if not destination:return
        developer=simpledialog.askstring("Exportar pacote","Nome do publicador (mesmo usuário da sua conta BLOOM):",parent=self)
        if not developer:return
        try:
            exported=json.loads(json.dumps(self.doc));files=[]
            def package_media(value):
                source=self._media_path(str(value or ""))
                if not source:raise ValueError(f"Não encontrei o arquivo de mídia: {value}")
                rel="assets/"+source.name;files.append(rel);return rel
            for obj in exported["scene"]["objects"]:
                if obj.get("image"):obj["image"]=package_media(obj["image"])
                for block in obj.get("blocks",[]):
                    if block.get("action")=="play_sound" and block.get("value"):block["value"]=package_media(block["value"])
            for asset in exported.get("assets",[]):
                if asset.get("type")=="audio":asset["path"]=package_media(asset["path"])
            exported.update({"name":exported.get("project",{}).get("name","Meu jogo"),"version":exported.get("project",{}).get("version","1.0.0"),"developer":developer,"description":"Projeto 2D do BLOOM MAKER","format":"bloom","files":sorted(set(files))})
            with zipfile.ZipFile(destination,"w",compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("bloom.json",json.dumps(exported,ensure_ascii=False,indent=2))
                written=set()
                for obj in exported["scene"]["objects"]:
                    for rel in [obj.get("image")]+[b.get("value") for b in obj.get("blocks",[]) if b.get("action")=="play_sound"]:
                        if rel and rel.startswith("assets/") and rel not in written:archive.write(self._media_path(rel),rel);written.add(rel)
                for asset in exported.get("assets",[]):
                    rel=asset.get("path","")
                    if rel.startswith("assets/") and rel not in written:archive.write(self._media_path(rel),rel);written.add(rel)
            messagebox.showinfo("Pacote exportado",f"ZIP criado em:\n{destination}\n\nEle contém bloom.json e os arquivos de mídia. O runtime jogável/exportador executável ainda é futuro; a prévia da engine é um protótipo 2D.",parent=self)
        except Exception as exc:messagebox.showerror("Falha ao exportar",str(exc),parent=self)

    def run_blocks(self, obj, trigger, canvas):
        for block in obj.get("blocks",[]):
            if block.get("trigger")!=trigger:continue
            action=block.get("action");value=block.get("value")
            if action=="move_x":obj["x"]=max(0,int(obj.get("x",0))+int(value))
            elif action=="move_y":obj["y"]=max(0,int(obj.get("y",0))+int(value))
            elif action=="say":obj["text"]=str(value)[:160];messagebox.showinfo(obj.get("name","Objeto"),str(value),parent=self)
            elif action=="set_color":obj["color"]=str(value)
            elif action=="play_sound":self.play_audio(str(value))
        if canvas is None:self.draw_scene()
        else:self._render_preview(canvas)

    def play_audio(self, relative):
        path=self._media_path(relative)
        if not path:messagebox.showwarning("Áudio",f"Arquivo de áudio não encontrado: {relative}",parent=self);return
        try:
            import pygame
            if not pygame.mixer.get_init():pygame.mixer.init()
            pygame.mixer.music.load(str(path));pygame.mixer.music.play()
        except Exception as exc:messagebox.showwarning("Áudio",f"Não foi possível tocar este arquivo: {exc}",parent=self)

    def _render_preview(self, canvas):
        canvas.delete("all");canvas.create_rectangle(0,0,960,540,fill=self.doc["scene"].get("background","#e7fcff"),outline="")
        refs=[]
        for i,obj in enumerate(self.doc["scene"]["objects"]):self._draw_object(canvas,obj,i,refs)
        canvas._image_refs=refs

    def preview(self):
        window=tk.Toplevel(self);window.title("Prévia jogável — BLOOM MAKER 2D");canvas=tk.Canvas(window,width=960,height=540,bg="#e7fcff",highlightthickness=0);canvas.pack();self._render_preview(canvas)
        def click(event):
            for item in reversed(canvas.find_overlapping(event.x,event.y,event.x,event.y)):
                tags=canvas.gettags(item)
                if tags and tags[0].isdigit():self.run_blocks(self.doc["scene"]["objects"][int(tags[0])],"click",canvas);break
        canvas.bind("<Button-1>",click)
        for obj in self.doc["scene"]["objects"]:self.run_blocks(obj,"start",canvas)
        ttk.Label(window,text="Protótipo 2D: blocos de evento, imagem e áudio. Engine 3D planejada para atualização futura.").pack(pady=8)
