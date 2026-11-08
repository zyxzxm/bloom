"""Cliente desktop BLOOM. Nunca executa automaticamente pacotes instalados."""
import json, os, shutil, subprocess, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import httpx
from .client import BloomClient
from bloom_safe.scanner import inspect_package
from bloom_safe.installer import safe_extract
try:
    from bloom_app.build_config import API_URL as BUILD_API_URL
except ImportError:
    BUILD_API_URL = ""

APP_NAME="BLOOM"
def data_home():
    root=Path(os.getenv("APPDATA", Path.home()))/"BLOOM"
    root.mkdir(parents=True,exist_ok=True)
    return root
DATA=data_home(); CONFIG=DATA/"settings.json"; STATE=DATA/"state.json"; GAMES=DATA/"games"
GAMES.mkdir(exist_ok=True)
DEFAULT={"api_url":BUILD_API_URL}

class BloomApp(tk.Tk):
    def __init__(self):
        super().__init__();self.client=BloomClient(CONFIG,STATE,DEFAULT);self.title("BLOOM — A world full of possibilities.");self.geometry("1120x760");self.minsize(820,600);self.configure(bg="#c9f5ff")
        self.style=ttk.Style(self);self.style.theme_use("clam");self.style.configure("TNotebook",background="#c9f5ff",borderwidth=0);self.style.configure("TNotebook.Tab",padding=(18,10),font=("Segoe UI",11,"bold"),background="#a6eced");self.style.map("TNotebook.Tab",background=[("selected","#ffffff")]);self.style.configure("TButton",font=("Segoe UI",10,"bold"),padding=8,background="#3ec9d6",foreground="#063c54");self.style.map("TButton",background=[("active","#ffb65c")]);self.style.configure("Treeview",rowheight=30,font=("Segoe UI",10));self.style.configure("Treeview.Heading",font=("Segoe UI",10,"bold"))
        self._header();self.tabs=ttk.Notebook(self);self.tabs.pack(fill="both",expand=True,padx=16,pady=12)
        self.home=self._tab("Início");self.garden=self._tab("BLOOM GARDEN");self.world=self._tab("BLOOM WORLD");self.library=self._tab("Minha biblioteca");self.profile=self._tab("Perfil");self.settings=self._tab("Configurações")
        self._build_home();self._build_garden();self._build_world();self._build_library();self._build_profile();self._build_settings();self.after(250,self.load_games)
    def _header(self):
        top=tk.Frame(self,bg="#23bcd0",height=100);top.pack(fill="x");top.pack_propagate(False)
        tk.Label(top,text="✿ BLOOM",font=("Segoe UI",29,"bold"),fg="white",bg="#23bcd0").pack(side="left",padx=22)
        tk.Label(top,text="A world full of possibilities.",font=("Segoe UI",13,"italic"),fg="#eaffff",bg="#23bcd0").pack(side="left",padx=8)
        self.user_label=tk.Label(top,text=self.client.state.get("user",{}).get("username","Visitante"),font=("Segoe UI",12,"bold"),fg="#ffffff",bg="#23bcd0");self.user_label.pack(side="right",padx=24)
    def _tab(self,name):
        f=tk.Frame(self.tabs,bg="#f6feff");self.tabs.add(f,text=name);return f
    def _heading(self,parent,title,subtitle):
        tk.Label(parent,text=title,font=("Segoe UI",23,"bold"),fg="#08798f",bg="#f6feff").pack(anchor="w",padx=22,pady=(18,2));tk.Label(parent,text=subtitle,font=("Segoe UI",10),fg="#42727b",bg="#f6feff").pack(anchor="w",padx=24,pady=(0,14))
    def _build_home(self):
        self._heading(self.home,"Bem-vindo ao seu jardim de jogos!","Descubra criações, encontre sua comunidade e cultive ideias.")
        hero=tk.Frame(self.home,bg="#d8fbef",highlightbackground="#76d7d2",highlightthickness=2);hero.pack(fill="x",padx=24,pady=8)
        tk.Label(hero,text="🌱  JOGAR • DESCOBRIR • CRIAR",font=("Segoe UI",22,"bold"),bg="#d8fbef",fg="#178b73").pack(anchor="w",padx=22,pady=(22,8));tk.Label(hero,text="BLOOM une seus jogos favoritos, uma loja comunitária e ferramentas para criar.",font=("Segoe UI",12),bg="#d8fbef",fg="#285c60").pack(anchor="w",padx=22,pady=(0,22))
        row=tk.Frame(self.home,bg="#f6feff");row.pack(fill="x",padx=24,pady=14)
        for title,desc,tab in [("🪴 BLOOM GARDEN","Explore e instale jogos publicados.",1),("🌐 BLOOM WORLD","Converse com a comunidade.",2),("🎨 BLOOM MAKER","Abra o editor visual 2D.","maker")]:
            card=tk.Frame(row,bg="#e8faff",highlightbackground="#b2e9ef",highlightthickness=1);card.pack(side="left",fill="both",expand=True,padx=6);tk.Label(card,text=title,font=("Segoe UI",14,"bold"),bg="#e8faff",fg="#08798f").pack(pady=(15,5));tk.Label(card,text=desc,bg="#e8faff",wraplength=220).pack(pady=5);ttk.Button(card,text="Abrir",command=(self.open_maker if tab=="maker" else lambda t=tab:self.tabs.select(t))).pack(pady=(5,15))
        ttk.Button(self.home,text="Entrar / criar conta",command=self.login_dialog).pack(anchor="w",padx=30,pady=12)
    def _build_garden(self):
        self._heading(self.garden,"🌼 BLOOM GARDEN","Uma estufa de jogos feitos pela comunidade.")
        bar=tk.Frame(self.garden,bg="#f6feff");bar.pack(fill="x",padx=24);self.search_var=tk.StringVar();tk.Entry(bar,textvariable=self.search_var,font=("Segoe UI",11),width=36).pack(side="left",ipady=6);self.category=tk.StringVar(value="todos");ttk.Combobox(bar,textvariable=self.category,values=["todos","exe","pygame","bloom"],state="readonly",width=12).pack(side="left",padx=8);ttk.Button(bar,text="Pesquisar",command=self.load_games).pack(side="left");ttk.Button(bar,text="Publicar pacote ZIP",command=self.publish_dialog).pack(side="right")
        self.game_table=ttk.Treeview(self.garden,columns=("format","version","developer","rating"),show="tree headings");self.game_table.heading("#0",text="Jogo");self.game_table.heading("format",text="Formato");self.game_table.heading("version",text="Versão");self.game_table.heading("developer",text="Desenvolvedor");self.game_table.heading("rating",text="Avaliação");self.game_table.column("#0",width=290);self.game_table.pack(fill="both",expand=True,padx=24,pady=12);self.game_table.bind("<Double-1>",lambda e:self.game_details())
        controls=tk.Frame(self.garden,bg="#f6feff");controls.pack(fill="x",padx=24,pady=(0,15));ttk.Button(controls,text="Detalhes",command=self.game_details).pack(side="left");ttk.Button(controls,text="Verificar e instalar",command=self.install_game).pack(side="left",padx=8)
    def _build_world(self):
        self._heading(self.world,"🌐 BLOOM WORLD","Uma comunidade real conectada à API que você configurar.")
        row=tk.Frame(self.world,bg="#f6feff");row.pack(fill="x",padx=24);self.post_var=tk.StringVar();tk.Entry(row,textvariable=self.post_var,font=("Segoe UI",11)).pack(side="left",fill="x",expand=True,ipady=8);ttk.Button(row,text="Publicar",command=self.create_post).pack(side="left",padx=8)
        ttk.Button(self.world,text="Atualizar feed",command=self.load_posts).pack(anchor="w",padx=24,pady=8)
        self.posts=tk.Listbox(self.world,font=("Segoe UI",11),bg="white",fg="#164b59",selectbackground="#36bfd0",borderwidth=0);self.posts.pack(fill="both",expand=True,padx=24,pady=8);self.posts.bind("<Double-1>",self.post_action)
        ttk.Button(self.world,text="Curtir / comentar publicação selecionada",command=self.post_action).pack(anchor="w",padx=24,pady=(0,15))
    def _build_library(self):
        self._heading(self.library,"🎮 Minha biblioteca","Instalações locais. Nada será iniciado automaticamente.")
        self.lib=tk.Listbox(self.library,font=("Segoe UI",11),bg="white",borderwidth=0);self.lib.pack(fill="both",expand=True,padx=24,pady=10);row=tk.Frame(self.library,bg="#f6feff");row.pack(anchor="w",padx=24,pady=10);ttk.Button(row,text="Atualizar lista",command=self.refresh_library).pack(side="left");ttk.Button(row,text="Desinstalar selecionado",command=self.uninstall_game).pack(side="left",padx=8);ttk.Button(row,text="Abrir pasta de arquivos",command=lambda:os.startfile(str(GAMES)) if sys.platform=="win32" else messagebox.showinfo("Pasta",str(GAMES))).pack(side="left");self.refresh_library()
    def _build_profile(self):
        self._heading(self.profile,"👤 Perfil","Cadastre-se ou entre para publicar e participar.")
        self.profile_text=tk.Label(self.profile,text="Você está navegando como visitante.",font=("Segoe UI",13),bg="#f6feff",justify="left");self.profile_text.pack(anchor="w",padx=28,pady=12);row=tk.Frame(self.profile,bg="#f6feff");row.pack(anchor="w",padx=24);ttk.Button(row,text="Entrar",command=self.login_dialog).pack(side="left");ttk.Button(row,text="Criar conta",command=self.register_dialog).pack(side="left",padx=8);ttk.Button(row,text="Sair",command=self.logout).pack(side="left")
    def _build_settings(self):
        self._heading(self.settings,"⚙ Configurações","A URL deve ser HTTPS e apontar para seu backend BLOOM WORLD implantado.")
        tk.Label(self.settings,text="URL base da API",bg="#f6feff",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=26,pady=(12,4));self.api_var=tk.StringVar(value=self.client.base);tk.Entry(self.settings,textvariable=self.api_var,width=70,font=("Segoe UI",11)).pack(anchor="w",padx=26,ipady=6);ttk.Button(self.settings,text="Salvar URL",command=self.save_url).pack(anchor="w",padx=26,pady=10);ttk.Button(self.settings,text="Testar conexão",command=self.test_api).pack(anchor="w",padx=26);tk.Label(self.settings,text=f"Dados locais e jogos instalados ficam em: {DATA}\nVersão inicial: execução de jogos de terceiros não é isolada por sandbox do Windows. Use cautela.",bg="#f6feff",fg="#466b73",justify="left",wraplength=800).pack(anchor="w",padx=26,pady=20)
    def open_maker(self):
        from bloom_maker.editor import Maker
        Maker(self)
    def online(self,method,path,**kw):return self.client.request(method,path,**kw)
    def handle(self,fn):
        try:fn()
        except httpx.HTTPStatusError as e:messagebox.showerror("BLOOM WORLD",f"API respondeu {e.response.status_code}: {e.response.text[:500]}")
        except Exception as e:messagebox.showerror("BLOOM",str(e))
    def login_dialog(self):
        user=simpledialog.askstring("Entrar","Nome de usuário:",parent=self);password=simpledialog.askstring("Entrar","Senha:",show="*",parent=self)
        if user and password:self.handle(lambda:self._login(user,password))
    def _login(self,u,p):self.client.auth("login",{"username":u,"password":p});self.update_user();messagebox.showinfo("BLOOM","Login realizado!");self.load_posts()
    def register_dialog(self):
        u=simpledialog.askstring("Criar conta","Nome de usuário (3-32 letras, números ou _):",parent=self);email=simpledialog.askstring("Criar conta","E-mail:",parent=self);p=simpledialog.askstring("Criar conta","Senha (mínimo 10 caracteres):",show="*",parent=self)
        if u and email and p:self.handle(lambda:self._create_account(u,email,p))
    def _create_account(self,u,e,p):self.client.auth("register",{"username":u,"email":e,"password":p});self.update_user();messagebox.showinfo("BLOOM","Conta criada!")
    def update_user(self):self.user_label.config(text=self.client.state.get("user",{}).get("username","Visitante"));self.profile_text.config(text=json.dumps(self.client.state.get("user",{}),ensure_ascii=False,indent=2) if self.client.state.get("user") else "Você está navegando como visitante.")
    def logout(self):self.client.state={};STATE.unlink(missing_ok=True);self.update_user();messagebox.showinfo("BLOOM","Sessão encerrada.")
    def save_url(self):
        val=self.api_var.get().strip().rstrip("/")
        if not val.startswith("https://") and not val.startswith("http://127.0.0.1") and not val.startswith("http://localhost"):messagebox.showerror("URL inválida","Use HTTPS para servidor online.");return
        self.client.config={"api_url":val};CONFIG.write_text(json.dumps(self.client.config),encoding="utf-8");messagebox.showinfo("BLOOM","URL salva.")
    def test_api(self):self.handle(lambda:messagebox.showinfo("BLOOM WORLD",self.online("GET","/health").text))
    def load_games(self):
        def work():
            p={"q":self.search_var.get(),"category":"" if self.category.get()=="todos" else self.category.get()};r=self.online("GET","/api/games",params=p);r.raise_for_status();games=r.json();self.after(0,lambda:self.show_games(games))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def show_games(self,games):
        self.game_table.delete(*self.game_table.get_children());self.game_map={}
        for g in games:
            iid=self.game_table.insert("","end",text=g["name"],values=(g["format"],g["version"],g["developer"],f'{g["rating"]:.1f}' if g["rating"] else "—"));self.game_map[iid]=g
    def selected_game(self):
        sel=self.game_table.selection()
        if not sel:raise ValueError("Selecione um jogo no catálogo.")
        return self.game_map[sel[0]]
    def game_details(self):
        try:
            g=self.selected_game();messagebox.showinfo(g["name"],f'{g["description"]}\n\nDesenvolvedor: {g["developer"]}\nVersão: {g["version"]}\nFormato: {g["format"]}\nSHA-256: {g["sha256"]}')
        except Exception as e:messagebox.showerror("BLOOM GARDEN",str(e))
    def install_game(self):
        def work():
            g=self.selected_game();response=self.online("GET",f'/api/games/{g["slug"]}/download');response.raise_for_status();tmp=DATA/(g["slug"]+".zip");tmp.write_bytes(response.content);report=inspect_package(tmp)
            if report["sha256"]!=g["sha256"]:raise ValueError("Hash do pacote não corresponde ao catálogo. Instalação interrompida.")
            dest=GAMES/g["slug"]
            if dest.exists():shutil.rmtree(dest)
            safe_extract(tmp,dest);tmp.unlink(missing_ok=True);(dest/"security-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");self.after(0,self.refresh_library);self.after(0,lambda:messagebox.showwarning("BLOOM SAFE",f'Pacote instalado, não executado. Hash SHA-256 verificado.\nResultado: {report["summary"]}\n\nA verificação não garante segurança. Jogos de terceiros permanecem potencialmente perigosos.'))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def refresh_library(self):
        self.lib.delete(0,"end")
        for p in sorted(GAMES.iterdir()):
            if p.is_dir():self.lib.insert("end",p.name)
    def uninstall_game(self):
        sel=self.lib.curselection()
        if not sel:return
        p=GAMES/self.lib.get(sel[0])
        if messagebox.askyesno("Desinstalar",f"Remover {p.name} e todos os seus arquivos?"):shutil.rmtree(p,ignore_errors=True);self.refresh_library()
    def load_posts(self):
        def work():r=self.online("GET","/api/posts");r.raise_for_status();items=r.json();self.after(0,lambda:self.show_posts(items))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def show_posts(self,items):
        self.posts.delete(0,"end");self.post_map={}
        for p in items:
            self.posts.insert("end",f'✿ {p["author"]} · {p["created_at"]}\n{p["body"]}\n♥ {p["likes"]}   Comentários: {p["comments"]}\n');self.post_map[self.posts.size()-1]=p
    def create_post(self):
        text=self.post_var.get().strip()
        if not text:return
        self.handle(lambda:self._create_post(text))
    def _create_post(self,text):r=self.online("POST","/api/posts",json={"body":text});r.raise_for_status();self.post_var.set("");self.load_posts()
    def post_action(self,event=None):
        sel=self.posts.curselection()
        if not sel:return
        p=self.post_map[sel[0]]
        def act():
            r=self.online("POST",f'/api/posts/{p["id"]}/like');r.raise_for_status();self.load_posts()
            if messagebox.askyesno("Comentário","Curtir realizado. Deseja comentar?"):
                body=simpledialog.askstring("Comentário","Escreva seu comentário:",parent=self)
                if body:self.online("POST",f'/api/posts/{p["id"]}/comments',json={"body":body})
        self.handle(act)
    def publish_dialog(self):
        messagebox.showinfo("Publicar jogo","A API recebe pacote ZIP com bloom.json. Para reduzir risco, prepare o pacote fora do BLOOM, escaneie-o e leia a documentação. A publicação exige login.")
        path=filedialog.askopenfilename(filetypes=[("Pacote ZIP","*.zip")],parent=self)
        if not path:return
        name=simpledialog.askstring("Metadados","Nome do jogo:",parent=self);version=simpledialog.askstring("Metadados","Versão:",initialvalue="1.0.0",parent=self);fmt=simpledialog.askstring("Metadados","Formato: exe / pygame / bloom",parent=self)
        if not name or not version or fmt not in {"exe","pygame","bloom"}:messagebox.showerror("BLOOM","Metadados inválidos.");return
        self.handle(lambda:self._publish(path,name,version,fmt))
    def _publish(self,path,name,version,fmt):
        with open(path,"rb") as f:r=self.online("POST","/api/games",data={"name":name,"version":version,"description":"","format":fmt},files={"file":(Path(path).name,f,"application/zip")})
        r.raise_for_status();messagebox.showinfo("Publicado",r.text);self.load_games()

if __name__=="__main__":BloomApp().mainloop()
