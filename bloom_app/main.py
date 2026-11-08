"""Cliente desktop BLOOM. Nunca executa automaticamente pacotes instalados."""
import json, os, shutil, subprocess, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import httpx
from bloom_app.client import BloomClient
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
        super().__init__();self.client=BloomClient(CONFIG,STATE,DEFAULT);self.title("BLOOM — A world full of possibilities.");self.geometry("1180x800");self.minsize(900,650);self.configure(bg="#eef4f7")
        self.palette={"app":"#eef4f7","surface":"#ffffff","ink":"#173b46","muted":"#5d7881","primary":"#147d83","accent":"#20a99e","line":"#d7e4e9"}
        self.style=ttk.Style(self);self.style.theme_use("clam");self.style.configure("TNotebook",background=self.palette["app"],borderwidth=0);self.style.configure("TNotebook.Tab",padding=(20,12),font=("Segoe UI",10,"bold"),background="#dce9ed",foreground=self.palette["ink"]);self.style.map("TNotebook.Tab",background=[("selected",self.palette["surface"]),("active","#cce9e7")],foreground=[("selected",self.palette["primary"])]);self.style.configure("TButton",font=("Segoe UI",10,"bold"),padding=(13,9),background=self.palette["accent"],foreground="#ffffff",borderwidth=0);self.style.map("TButton",background=[("active",self.palette["primary"]),("disabled","#c7d4d9")],foreground=[("disabled","#71848a")]);self.style.configure("Treeview",rowheight=36,font=("Segoe UI",10),background=self.palette["surface"],fieldbackground=self.palette["surface"],foreground=self.palette["ink"],borderwidth=0);self.style.configure("Treeview.Heading",font=("Segoe UI",10,"bold"),background="#e4eef1",foreground=self.palette["ink"],padding=9);self.style.map("Treeview",background=[("selected","#c6eeea")],foreground=[("selected",self.palette["ink"])])
        self._header();self.tabs=ttk.Notebook(self);self.tabs.pack(fill="both",expand=True,padx=16,pady=12)
        self.home=self._tab("Início");self.garden=self._tab("BLOOM GARDEN");self.world=self._tab("BLOOM WORLD");self.library=self._tab("Minha biblioteca");self.profile=self._tab("Perfil");self.settings=self._tab("Configurações")
        self._build_home();self._build_garden();self._build_world();self._build_library();self._build_profile();self._build_settings();self.after(250,self.load_games)
    def _header(self):
        top=tk.Frame(self,bg="#123b46",height=92);top.pack(fill="x");top.pack_propagate(False)
        brand=tk.Frame(top,bg="#123b46");brand.pack(side="left",fill="y",padx=25)
        tk.Label(brand,text="✿  BLOOM",font=("Segoe UI",27,"bold"),fg="#ffffff",bg="#123b46").pack(side="left",pady=17)
        tk.Frame(top,bg="#2d5961",width=1,height=42).pack(side="left",padx=(5,17),pady=25)
        tk.Label(top,text="JOGUE  ·  DESCUBRA  ·  CRIE",font=("Segoe UI",10,"bold"),fg="#b9e6df",bg="#123b46").pack(side="left")
        self.user_label=tk.Label(top,text="●  "+self.client.state.get("user",{}).get("username","Visitante"),font=("Segoe UI",10,"bold"),fg="#eaffff",bg="#1a4c57",padx=14,pady=9);self.user_label.pack(side="right",padx=24)
    def _tab(self,name):
        f=tk.Frame(self.tabs,bg=self.palette["app"]);self.tabs.add(f,text=name);return f
    def _heading(self,parent,title,subtitle):
        tk.Label(parent,text=title,font=("Segoe UI",23,"bold"),fg=self.palette["ink"],bg=self.palette["app"]).pack(anchor="w",padx=26,pady=(22,3));tk.Label(parent,text=subtitle,font=("Segoe UI",10),fg=self.palette["muted"],bg=self.palette["app"]).pack(anchor="w",padx=28,pady=(0,16))
    def _build_home(self):
        self._heading(self.home,"Bem-vindo ao seu jardim de jogos!","Descubra criações, encontre sua comunidade e cultive ideias.")
        hero=tk.Frame(self.home,bg="#e2f6f2",highlightbackground="#a3dcd5",highlightthickness=2);hero.pack(fill="x",padx=24,pady=8)
        tk.Label(hero,text="🌱  JOGAR • DESCOBRIR • CRIAR",font=("Segoe UI",22,"bold"),bg="#e2f6f2",fg="#147d83").pack(anchor="w",padx=22,pady=(22,8));tk.Label(hero,text="BLOOM une seus jogos favoritos, uma loja comunitária e ferramentas para criar.",font=("Segoe UI",12),bg="#e2f6f2",fg="#355b63").pack(anchor="w",padx=22,pady=(0,22))
        row=tk.Frame(self.home,bg="#eef4f7");row.pack(fill="x",padx=24,pady=14)
        for title,desc,tab in [("🪴 BLOOM GARDEN","Explore e instale jogos publicados.",1),("🌐 BLOOM WORLD","Converse com a comunidade.",2),("🎨 BLOOM MAKER","Abra o editor visual 2D.","maker")]:
            card=tk.Frame(row,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);card.pack(side="left",fill="both",expand=True,padx=6);tk.Label(card,text=title,font=("Segoe UI",14,"bold"),bg="#ffffff",fg="#147d83").pack(pady=(15,5));tk.Label(card,text=desc,bg="#ffffff",wraplength=220).pack(pady=5);ttk.Button(card,text="Abrir",command=(self.open_maker if tab=="maker" else lambda t=tab:self.tabs.select(t))).pack(pady=(5,15))
        ttk.Button(self.home,text="Entrar / criar conta",command=self.login_dialog).pack(anchor="w",padx=30,pady=12)
    def _build_garden(self):
        self._heading(self.garden,"🌼 BLOOM GARDEN","Uma estufa de jogos feitos pela comunidade.")
        bar=tk.Frame(self.garden,bg="#eef4f7");bar.pack(fill="x",padx=24);self.search_var=tk.StringVar();tk.Entry(bar,textvariable=self.search_var,font=("Segoe UI",11),width=36).pack(side="left",ipady=6);self.category=tk.StringVar(value="todos");ttk.Combobox(bar,textvariable=self.category,values=["todos","exe","pygame","bloom"],state="readonly",width=12).pack(side="left",padx=8);ttk.Button(bar,text="Pesquisar",command=self.load_games).pack(side="left");ttk.Button(bar,text="Publicar pacote ZIP",command=self.publish_dialog).pack(side="right")
        self.game_table=ttk.Treeview(self.garden,columns=("format","version","developer","rating"),show="tree headings");self.game_table.heading("#0",text="Jogo");self.game_table.heading("format",text="Formato");self.game_table.heading("version",text="Versão");self.game_table.heading("developer",text="Desenvolvedor");self.game_table.heading("rating",text="Avaliação");self.game_table.column("#0",width=290);self.game_table.pack(fill="both",expand=True,padx=24,pady=12);self.game_table.bind("<Double-1>",lambda e:self.game_details())
        controls=tk.Frame(self.garden,bg="#eef4f7");controls.pack(fill="x",padx=24,pady=(0,15));ttk.Button(controls,text="Detalhes",command=self.game_details).pack(side="left");ttk.Button(controls,text="Verificar e instalar",command=self.install_game).pack(side="left",padx=8)
    def _build_world(self):
        self._heading(self.world,"🌐 BLOOM WORLD","Uma comunidade real conectada à API que você configurar.")
        composer=tk.Frame(self.world,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);composer.pack(fill="x",padx=26,pady=(0,12));self.post_var=tk.StringVar();tk.Entry(composer,textvariable=self.post_var,font=("Segoe UI",11),relief="flat",bg="#f5f8fa",fg="#173b46",insertbackground="#147d83").pack(side="left",fill="x",expand=True,padx=(14,8),pady=12,ipady=9);ttk.Button(composer,text="Publicar",command=self.create_post).pack(side="right",padx=12,pady=10)
        feedbar=tk.Frame(self.world,bg="#eef4f7");feedbar.pack(fill="x",padx=26,pady=(0,4));tk.Label(feedbar,text="PUBLICAÇÕES RECENTES",font=("Segoe UI",9,"bold"),fg="#5d7881",bg="#eef4f7").pack(side="left");ttk.Button(feedbar,text="Atualizar feed",command=self.load_posts).pack(side="right")
        feedbox=tk.Frame(self.world,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);feedbox.pack(fill="both",expand=True,padx=26,pady=(6,10));self.posts=tk.Listbox(feedbox,font=("Segoe UI",10),bg="#ffffff",fg="#173b46",selectbackground="#d7f1ed",selectforeground="#123b46",borderwidth=0,highlightthickness=0,activestyle="none",selectmode="browse");self.posts.pack(fill="both",expand=True,padx=8,pady=8);self.posts.bind("<Double-1>",self.view_comments)
        actions=tk.Frame(self.world,bg="#eef4f7");actions.pack(fill="x",padx=26,pady=(0,14));ttk.Button(actions,text="Curtir / descurtir",command=self.post_action).pack(side="left");ttk.Button(actions,text="Ver comentários / comentar",command=self.view_comments).pack(side="left",padx=9)
    def _build_library(self):
        self._heading(self.library,"🎮 Minha biblioteca","Instalações locais. Nada será iniciado automaticamente.")
        self.lib=tk.Listbox(self.library,font=("Segoe UI",11),bg="white",borderwidth=0);self.lib.pack(fill="both",expand=True,padx=24,pady=10);row=tk.Frame(self.library,bg="#eef4f7");row.pack(anchor="w",padx=24,pady=10);ttk.Button(row,text="Atualizar lista",command=self.refresh_library).pack(side="left");ttk.Button(row,text="Desinstalar selecionado",command=self.uninstall_game).pack(side="left",padx=8);ttk.Button(row,text="Abrir pasta de arquivos",command=lambda:os.startfile(str(GAMES)) if sys.platform=="win32" else messagebox.showinfo("Pasta",str(GAMES))).pack(side="left");self.refresh_library()
    def _build_profile(self):
        self._heading(self.profile,"👤 Perfil","Cadastre-se ou entre para publicar e participar.")
        self.profile_text=tk.Label(self.profile,text="Você está navegando como visitante.",font=("Segoe UI",13),bg="#eef4f7",justify="left");self.profile_text.pack(anchor="w",padx=28,pady=12);row=tk.Frame(self.profile,bg="#eef4f7");row.pack(anchor="w",padx=24);ttk.Button(row,text="Entrar",command=self.login_dialog).pack(side="left");ttk.Button(row,text="Criar conta",command=self.register_dialog).pack(side="left",padx=8);ttk.Button(row,text="Sair",command=self.logout).pack(side="left")
    def _build_settings(self):
        self._heading(self.settings,"⚙ Configurações","A URL deve ser HTTPS e apontar para seu backend BLOOM WORLD implantado.")
        tk.Label(self.settings,text="URL base da API",bg="#eef4f7",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=26,pady=(12,4));self.api_var=tk.StringVar(value=self.client.base);tk.Entry(self.settings,textvariable=self.api_var,width=70,font=("Segoe UI",11)).pack(anchor="w",padx=26,ipady=6);ttk.Button(self.settings,text="Salvar URL",command=self.save_url).pack(anchor="w",padx=26,pady=10);ttk.Button(self.settings,text="Testar conexão",command=self.test_api).pack(anchor="w",padx=26);tk.Label(self.settings,text=f"Dados locais e jogos instalados ficam em: {DATA}\nVersão inicial: execução de jogos de terceiros não é isolada por sandbox do Windows. Use cautela.",bg="#eef4f7",fg="#466b73",justify="left",wraplength=800).pack(anchor="w",padx=26,pady=20)
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
    def update_user(self):self.user_label.config(text="●  "+self.client.state.get("user",{}).get("username","Visitante"));self.profile_text.config(text=json.dumps(self.client.state.get("user",{}),ensure_ascii=False,indent=2) if self.client.state.get("user") else "Você está navegando como visitante.")
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
            word="comentário" if p["comments"]==1 else "comentários"
            self.posts.insert("end",f'✿  {p["author"]}   ·   {p["created_at"]}\n\n{p["body"]}\n\n♥  {p["likes"]}       ◉  {p["comments"]} {word}\n'+'─'*72+'\n');self.post_map[self.posts.size()-1]=p
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
        self.handle(act)
    def view_comments(self,event=None):
        sel=self.posts.curselection()
        if not sel:return
        post=self.post_map[sel[0]]
        def work():
            response=self.online("GET",f'/api/posts/{post["id"]}/comments');response.raise_for_status();items=response.json();self.after(0,lambda:self._show_comments(post,items))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def _show_comments(self,post,comments):
        window=tk.Toplevel(self);window.title(f'Comentários — {post["author"]}');window.geometry("620x570");window.minsize(480,420);window.configure(bg="#eef4f7");window.transient(self)
        tk.Label(window,text="Comentários",font=("Segoe UI",20,"bold"),fg="#173b46",bg="#eef4f7").pack(anchor="w",padx=22,pady=(18,0));tk.Label(window,text=f'Na publicação de {post["author"]}',font=("Segoe UI",10),fg="#5d7881",bg="#eef4f7").pack(anchor="w",padx=24,pady=(2,12))
        panel=tk.Frame(window,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);panel.pack(fill="both",expand=True,padx=22,pady=(0,12));scroll=tk.Scrollbar(panel);scroll.pack(side="right",fill="y");display=tk.Text(panel,wrap="word",font=("Segoe UI",10),bg="#ffffff",fg="#173b46",relief="flat",borderwidth=0,padx=16,pady=14,yscrollcommand=scroll.set,state="disabled");display.pack(fill="both",expand=True);scroll.config(command=display.yview);display.tag_configure("author",font=("Segoe UI",10,"bold"),foreground="#147d83");display.tag_configure("body",spacing1=4,spacing3=12)
        def render(items):
            display.configure(state="normal");display.delete("1.0","end")
            if not items:display.insert("end","Ainda não há comentários. Seja a primeira pessoa a comentar!", "body")
            for item in items:
                display.insert("end",f'{item["author"]}  ·  {item["created_at"]}\n',"author");display.insert("end",item["body"]+"\n\n","body")
            display.configure(state="disabled")
        render(comments)
        composer=tk.Frame(window,bg="#eef4f7");composer.pack(fill="x",padx=22,pady=(0,18));entry=tk.Text(composer,height=3,wrap="word",font=("Segoe UI",10),bg="#ffffff",fg="#173b46",relief="solid",borderwidth=1,highlightthickness=1,highlightbackground="#d7e4e9");entry.pack(side="left",fill="x",expand=True,padx=(0,10))
        def refresh_comments():
            def work():
                response=self.online("GET",f'/api/posts/{post["id"]}/comments');response.raise_for_status();items=response.json();self.after(0,lambda:render(items))
            threading.Thread(target=lambda:self.handle(work),daemon=True).start()
        def send_comment():
            body=entry.get("1.0","end").strip()
            if not body:return
            if not (self.client.state.get("access_token") or self.client.state.get("token")):
                messagebox.showinfo("Entre para comentar","Faça login no Perfil para enviar um comentário.",parent=window);return
            def work():
                response=self.online("POST",f'/api/posts/{post["id"]}/comments',json={"body":body});response.raise_for_status();self.after(0,lambda:(entry.delete("1.0","end"),self.load_posts(),refresh_comments()))
            threading.Thread(target=lambda:self.handle(work),daemon=True).start()
        ttk.Button(composer,text="Enviar",command=send_comment).pack(side="right",fill="y")
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
