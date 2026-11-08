"""Editor de cenas BLOOM MAKER v1: dados independentes do renderer 2D."""
import json, tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from pathlib import Path

DEFAULT={"maker_version":1,"project":{"name":"Meu jogo","version":"1.0.0","format":"bloom"},"scene":{"name":"Cena 1","width":960,"height":540,"objects":[]}}
class Maker(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent);self.title("BLOOM MAKER — editor 2D");self.geometry("1024x700");self.configure(bg="#d7f7ff");self.doc=json.loads(json.dumps(DEFAULT));self.path=None
        bar=tk.Frame(self,bg="#22afc4");bar.pack(fill="x")
        for text,cmd in [("Novo objeto",self.add_object),("Excluir",self.delete_object),("Abrir",self.open_file),("Salvar",self.save_file),("Testar cena",self.preview)]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=5,pady=7)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=10,pady=10);left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=1);pane.add(right,weight=4)
        ttk.Label(left,text="Objetos da cena",font=("Segoe UI",12,"bold")).pack(anchor="w");self.objects=ttk.Treeview(left,columns=("type",),show="tree headings");self.objects.heading("#0",text="Objeto");self.objects.heading("type",text="Tipo");self.objects.pack(fill="both",expand=True);self.objects.bind("<<TreeviewSelect>>",self.select_object)
        self.canvas=tk.Canvas(right,bg="#b5f3ff",highlightbackground="#7dd9dc",highlightthickness=2);self.canvas.pack(fill="both",expand=True);self.canvas.bind("<Button-1>",self.canvas_click)
        form=ttk.Frame(right);form.pack(fill="x",pady=8);self.vars={}
        for label,key in [("Nome","name"),("X","x"),("Y","y"),("Largura","width"),("Altura","height"),("Cor","color")]:
            ttk.Label(form,text=label).pack(side="left",padx=(5,2));v=tk.StringVar();entry=ttk.Entry(form,textvariable=v,width=10);entry.pack(side="left");entry.bind("<FocusOut>",self.apply_properties);entry.bind("<Return>",self.apply_properties);self.vars[key]=v
        ttk.Button(form,text="Aplicar",command=self.apply_properties).pack(side="left",padx=6);self.refresh()
    def selected(self):
        sel=self.objects.selection()
        if not sel:return None
        try:return self.doc["scene"]["objects"][int(sel[0])]
        except (ValueError,IndexError):return None
    def add_object(self):
        n=len(self.doc["scene"]["objects"])+1;self.doc["scene"]["objects"].append({"name":f"Objeto {n}","type":"rect","x":80+n*12,"y":80+n*12,"width":100,"height":70,"color":"#ff9b50","events":[]});self.refresh();self.objects.selection_set(str(n-1));self.select_object()
    def delete_object(self):
        sel=self.objects.selection()
        if sel:self.doc["scene"]["objects"].pop(int(sel[0]));self.refresh()
    def refresh(self):
        self.objects.delete(*self.objects.get_children())
        for i,o in enumerate(self.doc["scene"]["objects"]):self.objects.insert("","end",iid=str(i),text=o["name"],values=(o.get("type","rect"),))
        self.draw_scene()
    def select_object(self,event=None):
        o=self.selected()
        if o:
            for k,v in self.vars.items():v.set(str(o.get(k,"")))
    def apply_properties(self,event=None):
        o=self.selected()
        if not o:return
        try:
            o["name"]=self.vars["name"].get()[:80]
            for k in ("x","y","width","height"):o[k]=max(0,min(10000,int(self.vars[k].get())))
            o["color"]=self.vars["color"].get()
            self.refresh();self.objects.selection_set(str(self.doc["scene"]["objects"].index(o)))
        except ValueError:messagebox.showerror("Propriedade inválida","X, Y, largura e altura devem ser inteiros.",parent=self)
    def draw_scene(self):
        self.canvas.delete("all");self.canvas.create_rectangle(4,4,964,544,fill="#e7fcff",outline="#35b9c6",width=3)
        for i,o in enumerate(self.doc["scene"]["objects"]):
            x,y,w,h=(int(o.get(k,0)) for k in ("x","y","width","height"));fill=o.get("color","#ff9b50");self.canvas.create_oval(x,y,x+w,y+h,fill=fill,outline="white",width=3,tags=(str(i),)) if o.get("type")=="ellipse" else self.canvas.create_rectangle(x,y,x+w,y+h,fill=fill,outline="white",width=3,tags=(str(i),));self.canvas.create_text(x+w/2,y+h/2,text=o.get("name","Objeto"),fill="#164b59",tags=(str(i),))
    def canvas_click(self,event):
        item=self.canvas.find_withtag("current")
        if item:
            tags=self.canvas.gettags(item[0])
            if tags and tags[0].isdigit():self.objects.selection_set(tags[0]);self.select_object()
    def open_file(self):
        p=filedialog.askopenfilename(filetypes=[("Projeto BLOOM","*.bloom.json"),("JSON","*.json")],parent=self)
        if p:
            try:
                d=json.loads(Path(p).read_text(encoding="utf-8"));self.validate(d);self.doc=d;self.path=Path(p);self.refresh()
            except Exception as e:messagebox.showerror("Não foi possível abrir",str(e),parent=self)
    def validate(self,d):
        if not isinstance(d.get("scene",{}).get("objects"),list):raise ValueError("Arquivo sem lista scene.objects")
        for o in d["scene"]["objects"]:
            for k in ("x","y","width","height"):int(o[k])
    def save_file(self):
        p=self.path or filedialog.asksaveasfilename(defaultextension=".bloom.json",filetypes=[("Projeto BLOOM","*.bloom.json")],parent=self)
        if p:self.path=Path(p);self.path.write_text(json.dumps(self.doc,ensure_ascii=False,indent=2),encoding="utf-8");messagebox.showinfo("BLOOM MAKER","Projeto salvo. Inclua este arquivo como bloom.json em um ZIP para publicar.",parent=self)
    def preview(self):
        w=tk.Toplevel(self);w.title("Prévia da cena — BLOOM MAKER");c=tk.Canvas(w,width=960,height=540,bg="#e7fcff");c.pack()
        for o in self.doc["scene"]["objects"]:
            x,y,ww,h=(int(o.get(k,0)) for k in ("x","y","width","height"));coords=(x,y,x+ww,y+h);(c.create_oval if o.get("type")=="ellipse" else c.create_rectangle)(*coords,fill=o.get("color","#ff9b50"),outline="white",width=3);c.create_text(x+ww/2,y+h/2,text=o.get("name","Objeto"),fill="#164b59")
        tk.Label(w,text="Prévia estática. Runtime de física, colisões, áudio e exportação executável serão etapas futuras.").pack()
