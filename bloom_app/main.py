"""Cliente desktop BLOOM. Nunca executa automaticamente pacotes instalados."""
import json, os, shutil, subprocess, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import httpx
from bloom_app.client import BloomClient
from bloom_safe.scanner import inspect_package
from bloom_safe.installer import safe_extract
from bloom_app.localization import LANGUAGES, translate
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
        self.home=self._tab("Início");self.garden=self._tab("BLOOM GARDEN");self.world=self._tab("BLOOM WORLD");self.messages=self._tab("Mensagens");self.library=self._tab("Minha biblioteca");self.profile=self._tab("Perfil");self.settings=self._tab("Configurações")
        self._build_home();self._build_garden();self._build_world();self._build_messages();self._build_library();self._build_profile();self._build_settings();self.language_var.set(f'{self.client.config.get("language","pt-BR")} — {LANGUAGES.get(self.client.config.get("language","pt-BR"),LANGUAGES["pt-BR"])}');self.apply_language();self.after(250,self.load_games)
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
        controls=tk.Frame(self.garden,bg="#eef4f7");controls.pack(fill="x",padx=24,pady=(0,15));ttk.Button(controls,text="Detalhes",command=self.game_details).pack(side="left");ttk.Button(controls,text="Verificar e instalar",command=self.install_game).pack(side="left",padx=8);ttk.Button(controls,text="Trocar capa do meu projeto",command=self.change_game_cover).pack(side="left",padx=8);ttk.Button(controls,text="Apagar meu projeto",command=self.delete_my_game).pack(side="right")
    def _build_world(self):
        self._heading(self.world,"🌐 BLOOM WORLD","Uma comunidade real conectada à API que você configurar.")
        composer=tk.Frame(self.world,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);composer.pack(fill="x",padx=26,pady=(0,12));self.post_var=tk.StringVar();tk.Entry(composer,textvariable=self.post_var,font=("Segoe UI",11),relief="flat",bg="#f5f8fa",fg="#173b46",insertbackground="#147d83").pack(side="left",fill="x",expand=True,padx=(14,8),pady=12,ipady=9);ttk.Button(composer,text="Publicar",command=self.create_post).pack(side="right",padx=12,pady=10)
        feedbar=tk.Frame(self.world,bg="#eef4f7");feedbar.pack(fill="x",padx=26,pady=(0,4));tk.Label(feedbar,text="PUBLICAÇÕES RECENTES",font=("Segoe UI",9,"bold"),fg="#5d7881",bg="#eef4f7").pack(side="left");ttk.Button(feedbar,text="Atualizar feed",command=self.load_posts).pack(side="right")
        feedbox=tk.Frame(self.world,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);feedbox.pack(fill="both",expand=True,padx=26,pady=(6,10));self.posts=tk.Listbox(feedbox,font=("Segoe UI",10),bg="#ffffff",fg="#173b46",selectbackground="#d7f1ed",selectforeground="#123b46",borderwidth=0,highlightthickness=0,activestyle="none",selectmode="browse");self.posts.pack(fill="both",expand=True,padx=8,pady=8);self.posts.bind("<Double-1>",self.view_comments)
        actions=tk.Frame(self.world,bg="#eef4f7");actions.pack(fill="x",padx=26,pady=(0,14));ttk.Button(actions,text="Curtir / descurtir",command=self.post_action).pack(side="left");ttk.Button(actions,text="Ver comentários / comentar",command=self.view_comments).pack(side="left",padx=9);ttk.Button(actions,text="Apagar minha publicação",command=self.delete_my_post).pack(side="right")
    def _build_messages(self):
        self._heading(self.messages,"Mensagens","Conversas diretas e em grupo. Mensagens não têm criptografia ponta a ponta.")
        bar=tk.Frame(self.messages,bg="#eef4f7");bar.pack(fill="x",padx=24,pady=(0,10));ttk.Button(bar,text="Nova conversa",command=self.new_direct_chat).pack(side="left");ttk.Button(bar,text="Criar grupo",command=self.new_group_chat).pack(side="left",padx=8);ttk.Button(bar,text="Atualizar",command=self.load_chats).pack(side="right")
        area=tk.Frame(self.messages,bg="#eef4f7");area.pack(fill="both",expand=True,padx=24,pady=4);left=tk.Frame(area,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);left.pack(side="left",fill="y",padx=(0,10));self.chat_list=tk.Listbox(left,width=28,font=("Segoe UI",10),bg="#ffffff",fg="#173b46",borderwidth=0,highlightthickness=0,selectbackground="#d7f1ed",activestyle="none");self.chat_list.pack(fill="both",expand=True,padx=5,pady=5);self.chat_list.bind("<<ListboxSelect>>",self.select_chat)
        right=tk.Frame(area,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);right.pack(side="left",fill="both",expand=True);self.chat_history=tk.Listbox(right,font=("Segoe UI",10),bg="#ffffff",fg="#173b46",borderwidth=0,highlightthickness=0,selectbackground="#d7f1ed",activestyle="none");self.chat_history.pack(fill="both",expand=True,padx=10,pady=10);composer=tk.Frame(right,bg="#eef4f7");composer.pack(fill="x",padx=10,pady=(0,10));self.chat_entry=tk.StringVar();tk.Entry(composer,textvariable=self.chat_entry,font=("Segoe UI",10),relief="flat",bg="#ffffff").pack(side="left",fill="x",expand=True,ipady=9,padx=(0,8));ttk.Button(composer,text="Enviar",command=self.send_chat_message).pack(side="right");ttk.Button(composer,text="Apagar minha mensagem",command=self.delete_chat_message).pack(side="right",padx=8);ttk.Button(composer,text="Denunciar",command=self.report_chat_message).pack(side="right",padx=8)
    def load_chats(self):
        def work():
            response=self.online("GET","/api/chats");response.raise_for_status();items=response.json();self.after(0,lambda:self.show_chats(items))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def show_chats(self,items):
        self.chat_list.delete(0,"end");self.chat_map={}
        for chat in items:
            title=chat["title"] or ", ".join(chat["members"])
            if chat["is_group"]:title="👥 "+title
            self.chat_list.insert("end",title);self.chat_map[self.chat_list.size()-1]=chat
    def new_direct_chat(self):
        username=simpledialog.askstring("Nova conversa","Nome de usuário:",parent=self)
        if not username:return
        def work():
            response=self.online("POST","/api/chats/direct",json={"username":username});response.raise_for_status();self.after(0,lambda:(self.load_chats(),setattr(self,"current_chat_id",response.json()["id"])))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def new_group_chat(self):
        title=simpledialog.askstring("Criar grupo","Nome do grupo:",parent=self)
        if not title:return
        names=simpledialog.askstring("Participantes","Digite pelo menos dois nomes de usuário separados por vírgula:",parent=self)
        if not names:return
        usernames=[name.strip() for name in names.split(",") if name.strip()]
        def work():
            response=self.online("POST","/api/chats/groups",json={"title":title,"usernames":usernames});response.raise_for_status();self.after(0,lambda:self.load_chats())
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def select_chat(self,event=None):
        selection=self.chat_list.curselection()
        if not selection:return
        chat=self.chat_map[selection[0]];self.current_chat_id=chat["id"];self.load_chat_messages()
    def load_chat_messages(self):
        chat_id=getattr(self,"current_chat_id",None)
        if not chat_id:return
        def work():
            response=self.online("GET",f"/api/chats/{chat_id}/messages");response.raise_for_status();items=response.json();self.after(0,lambda:self.show_chat_messages(items))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def show_chat_messages(self,items):
        self.chat_history.delete(0,"end");self.chat_message_map={}
        me=self.client.state.get("user",{}).get("id")
        for item in items:
            self.chat_history.insert("end",f'{item["sender"]}: {item["body"]}   ·   {item["created_at"]}');self.chat_message_map[self.chat_history.size()-1]=item
        if items:self.chat_history.see("end")
    def send_chat_message(self):
        chat_id=getattr(self,"current_chat_id",None);body=self.chat_entry.get().strip()
        if not chat_id or not body:return
        def work():
            response=self.online("POST",f"/api/chats/{chat_id}/messages",json={"body":body});response.raise_for_status();self.after(0,lambda:(self.chat_entry.set(""),self.load_chat_messages()))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def delete_chat_message(self):
        selection=self.chat_history.curselection();chat_id=getattr(self,"current_chat_id",None)
        if not selection or not chat_id:return
        msg=self.chat_message_map[selection[0]]
        if msg["sender_id"]!=self.client.state.get("user",{}).get("id"):
            messagebox.showinfo("Mensagens","Você só pode apagar mensagens enviadas por você.");return
        if not messagebox.askyesno("Apagar mensagem","Apagar esta mensagem para todos os participantes?"):return
        def work():
            response=self.online("DELETE",f"/api/chats/{chat_id}/messages/{msg['id']}");response.raise_for_status();self.after(0,self.load_chat_messages)
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def report_chat_message(self):
        selection=self.chat_history.curselection()
        if not selection or selection[0] not in self.chat_message_map:return
        msg=self.chat_message_map[selection[0]];reason=simpledialog.askstring("Denunciar mensagem","Explique o motivo (mínimo 5 caracteres):",parent=self)
        if not reason or len(reason.strip())<5:return
        def work():
            response=self.online("POST","/api/reports",json={"target_type":"message","target_id":msg["id"],"reason":reason.strip()});response.raise_for_status();self.after(0,lambda:messagebox.showinfo("Denúncia","Obrigado. O relato foi enviado para revisão."))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def delete_my_game(self):
        try:game=self.selected_game()
        except Exception as exc:messagebox.showerror("BLOOM GARDEN",str(exc));return
        if game.get("developer_id")!=self.client.state.get("user",{}).get("id"):
            messagebox.showinfo("BLOOM GARDEN","Só é possível apagar os projetos publicados pela sua própria conta.");return
        if not messagebox.askyesno("Apagar projeto",f'Apagar "{game["name"]}" publicado? Esta ação não pode ser desfeita.'):return
        def work():
            response=self.online("DELETE",f'/api/games/{game["id"]}');response.raise_for_status();self.after(0,self.load_games)
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def _build_library(self):
        self._heading(self.library,"🎮 Minha biblioteca","Instalações locais. Nada será iniciado automaticamente.")
        self.lib=tk.Listbox(self.library,font=("Segoe UI",11),bg="white",borderwidth=0);self.lib.pack(fill="both",expand=True,padx=24,pady=10);row=tk.Frame(self.library,bg="#eef4f7");row.pack(anchor="w",padx=24,pady=10);ttk.Button(row,text="Atualizar lista",command=self.refresh_library).pack(side="left");ttk.Button(row,text="Desinstalar selecionado",command=self.uninstall_game).pack(side="left",padx=8);ttk.Button(row,text="Abrir pasta de arquivos",command=lambda:os.startfile(str(GAMES)) if sys.platform=="win32" else messagebox.showinfo("Pasta",str(GAMES))).pack(side="left");self.refresh_library()
    def _build_profile(self):
        self._heading(self.profile,"👤 Perfil","Cadastre-se ou entre para publicar e participar.")
        self.avatar_display=tk.Label(self.profile,text="Sem foto",font=("Segoe UI",10),fg="#5d7881",bg="#eef4f7");self.avatar_display.pack(anchor="w",padx=28,pady=(4,0));self.profile_text=tk.Label(self.profile,text="Você está navegando como visitante.",font=("Segoe UI",13),bg="#eef4f7",justify="left");self.profile_text.pack(anchor="w",padx=28,pady=12);row=tk.Frame(self.profile,bg="#eef4f7");row.pack(anchor="w",padx=24);ttk.Button(row,text="Entrar",command=self.login_dialog).pack(side="left");ttk.Button(row,text="Criar conta",command=self.register_dialog).pack(side="left",padx=8);ttk.Button(row,text="Sair",command=self.logout).pack(side="left");ttk.Button(row,text="Adicionar / trocar foto de perfil",command=self.upload_avatar).pack(side="left",padx=8)
    def _build_settings(self):
        self._heading(self.settings,"⚙ Configurações","A URL deve ser HTTPS e apontar para seu backend BLOOM WORLD implantado.")
        tk.Label(self.settings,text="Idioma da interface",bg="#eef4f7",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=26,pady=(8,4));self.language_var=tk.StringVar(value="pt-BR");self.language_box=ttk.Combobox(self.settings,textvariable=self.language_var,values=[f"{code} — {name}" for code,name in LANGUAGES.items()],state="readonly",width=32);self.language_box.pack(anchor="w",padx=26);self.language_box.set(f"pt-BR — {LANGUAGES['pt-BR']}");self.language_box.bind("<<ComboboxSelected>>",self.change_language)
        tk.Label(self.settings,text="URL base da API",bg="#eef4f7",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=26,pady=(12,4));self.api_var=tk.StringVar(value=self.client.base);tk.Entry(self.settings,textvariable=self.api_var,width=70,font=("Segoe UI",11)).pack(anchor="w",padx=26,ipady=6);ttk.Button(self.settings,text="Salvar URL",command=self.save_url).pack(anchor="w",padx=26,pady=10);ttk.Button(self.settings,text="Testar conexão",command=self.test_api).pack(anchor="w",padx=26);tk.Label(self.settings,text=f"Dados locais e jogos instalados ficam em: {DATA}\nVersão inicial: execução de jogos de terceiros não é isolada por sandbox do Windows. Use cautela.",bg="#eef4f7",fg="#466b73",justify="left",wraplength=800).pack(anchor="w",padx=26,pady=20)
    def change_language(self,event=None):
        value=self.language_var.get().split(" — ",1)[0]
        if value not in LANGUAGES:return
        self.client.config["language"]=value;CONFIG.write_text(json.dumps(self.client.config,ensure_ascii=False),encoding="utf-8");self.apply_language();self.language_var.set(f"{value} — {LANGUAGES[value]}")
    def apply_language(self):
        language=self.client.config.get("language","pt-BR")
        def visit(widget):
            try:
                original=getattr(widget,"_bloom_original_text",None)
                if original is None:
                    original=widget.cget("text")
                    widget._bloom_original_text=original
                if original:widget.configure(text=translate(str(original),language))
            except (tk.TclError,AttributeError):pass
            for child in widget.winfo_children():visit(child)
        visit(self)
        for tab in self.tabs.tabs():
            original=self.tabs.tab(tab,"text")
            if not hasattr(self.tabs,"_bloom_tab_originals"):self.tabs._bloom_tab_originals={t:self.tabs.tab(t,"text") for t in self.tabs.tabs()}
            original=self.tabs._bloom_tab_originals.get(tab,original);self.tabs.tab(tab,text=translate(original,language))
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
        if not self.show_terms_dialog():return
        u=simpledialog.askstring("Criar conta","Nome de usuário (3-32 letras, números ou _):",parent=self);email=simpledialog.askstring("Criar conta","E-mail:",parent=self);p=simpledialog.askstring("Criar conta","Senha (mínimo 10 caracteres):",show="*",parent=self)
        if u and email and p:self.handle(lambda:self._create_account(u,email,p))
    def show_terms_dialog(self):
        try:
            response=self.online("GET","/api/terms");response.raise_for_status();terms=response.json()
        except Exception as exc:messagebox.showerror("Termos de uso",f"Não foi possível carregar os termos do servidor: {exc}");return False
        window=tk.Toplevel(self);window.title(f'Termos de uso BLOOM — v{terms["version"]}');window.geometry("700x600");window.transient(self);window.grab_set();tk.Label(window,text="Leia os termos de uso",font=("Segoe UI",17,"bold")).pack(anchor="w",padx=16,pady=(16,8));text=tk.Text(window,wrap="word",font=("Segoe UI",10),height=25);text.pack(fill="both",expand=True,padx=16);text.insert("1.0",terms["text"]);text.configure(state="disabled");result={"accepted":False};buttons=tk.Frame(window);buttons.pack(fill="x",padx=16,pady=14)
        def accept():result["accepted"]=True;window.destroy()
        ttk.Button(buttons,text="Li e aceito",command=accept).pack(side="right");ttk.Button(buttons,text="Não aceito",command=window.destroy).pack(side="right",padx=8);window.wait_window();return result["accepted"]
    def _create_account(self,u,e,p):self.client.auth("register",{"username":u,"email":e,"password":p,"accept_terms":True});self.update_user();messagebox.showinfo("BLOOM","Conta criada!")
    def upload_avatar(self):
        if not self.client.state.get("access_token"):messagebox.showinfo("Perfil","Entre na sua conta antes de adicionar uma foto.");return
        path=filedialog.askopenfilename(parent=self,filetypes=[("Imagens","*.png *.jpg *.jpeg *.webp *.gif")])
        if not path:return
        def work():
            with open(path,"rb") as media:response=self.online("PUT","/api/me/avatar",files={"file":(Path(path).name,media,"application/octet-stream")})
            response.raise_for_status();self.after(0,lambda:(self.load_avatar(self.client.state.get("user",{}).get("username","")),messagebox.showinfo("Perfil","Foto de perfil atualizada.")))
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
    def update_user(self):
        user=self.client.state.get("user",{});self.user_label.config(text="●  "+user.get("username","Visitante"));self.profile_text.config(text=json.dumps(user,ensure_ascii=False,indent=2) if user else "Você está navegando como visitante.")
        if user.get("username"):self.load_avatar(user["username"])
        elif hasattr(self,"avatar_display"):self.avatar_display.configure(image="",text="Sem foto");self.avatar_display.image=None
    def load_avatar(self,username):
        def work():
            try:
                import io
                from PIL import Image,ImageTk
                response=self.online("GET",f"/api/users/{username}/avatar")
                if response.status_code!=200:return
                image=Image.open(io.BytesIO(response.content));image.thumbnail((112,112));photo=ImageTk.PhotoImage(image);self.after(0,lambda:(self.avatar_display.configure(image=photo,text=""),setattr(self.avatar_display,"image",photo)))
            except Exception:pass
        threading.Thread(target=work,daemon=True).start()
    def logout(self):self.client.state={};STATE.unlink(missing_ok=True);self.update_user();messagebox.showinfo("BLOOM","Sessão encerrada.")
    def save_url(self):
        val=self.api_var.get().strip().rstrip("/")
        if not val.startswith("https://") and not val.startswith("http://127.0.0.1") and not val.startswith("http://localhost"):messagebox.showerror("URL inválida","Use HTTPS para servidor online.");return
        self.client.config.update({"api_url":val});CONFIG.write_text(json.dumps(self.client.config,ensure_ascii=False),encoding="utf-8");messagebox.showinfo("BLOOM","URL salva.")
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
            g=self.selected_game();window=tk.Toplevel(self);window.title(g["name"]);window.geometry("560x520");window.configure(bg="#eef4f7");tk.Label(window,text=g["name"],font=("Segoe UI",20,"bold"),fg="#173b46",bg="#eef4f7").pack(anchor="w",padx=20,pady=(18,5));cover=tk.Label(window,bg="#ffffff");cover.pack(fill="x",padx=20,pady=6);tk.Label(window,text=f'{g["description"]}\n\nDesenvolvedor: {g["developer"]}\nVersão: {g["version"]}\nFormato: {g["format"]}\nSHA-256: {g["sha256"]}',justify="left",anchor="w",wraplength=510,bg="#eef4f7",fg="#355b63").pack(fill="both",expand=True,padx=20,pady=10)
            if g.get("cover_url"):
                def load_cover():
                    try:
                        import io
                        from PIL import Image,ImageTk
                        response=self.online("GET",g["cover_url"]);response.raise_for_status();image=Image.open(io.BytesIO(response.content));image.thumbnail((500,220));photo=ImageTk.PhotoImage(image);self.after(0,lambda:(cover.configure(image=photo),setattr(cover,"image",photo)))
                    except Exception:pass
                threading.Thread(target=load_cover,daemon=True).start()
        except Exception as e:messagebox.showerror("BLOOM GARDEN",str(e))
    def change_game_cover(self):
        try:game=self.selected_game()
        except Exception as exc:messagebox.showerror("BLOOM GARDEN",str(exc));return
        if game.get("developer_id")!=self.client.state.get("user",{}).get("id"):
            messagebox.showinfo("Capa do projeto","Só o autor pode trocar a capa deste projeto.");return
        path=filedialog.askopenfilename(parent=self,filetypes=[("Imagens","*.png *.jpg *.jpeg *.webp *.gif")])
        if not path:return
        def work():
            with open(path,"rb") as image:response=self.online("PUT",f'/api/games/{game["id"]}/cover',files={"file":(Path(path).name,image,"application/octet-stream")})
            response.raise_for_status();self.after(0,self.load_games)
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
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
    def delete_my_post(self):
        sel=self.posts.curselection()
        if not sel:return
        post=self.post_map[sel[0]]
        if post.get("author_id")!=self.client.state.get("user",{}).get("id"):
            messagebox.showinfo("BLOOM WORLD","Só é possível apagar uma publicação feita pela sua conta.");return
        if not messagebox.askyesno("Apagar publicação","Apagar esta publicação e todos os comentários dela?"):return
        def work():
            response=self.online("DELETE",f'/api/posts/{post["id"]}');response.raise_for_status();self.after(0,self.load_posts)
        threading.Thread(target=lambda:self.handle(work),daemon=True).start()
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
        panel=tk.Frame(window,bg="#ffffff",highlightbackground="#d7e4e9",highlightthickness=1);panel.pack(fill="both",expand=True,padx=22,pady=(0,12));scroll=tk.Scrollbar(panel);scroll.pack(side="right",fill="y");display=tk.Listbox(panel,selectmode="browse",font=("Segoe UI",10),bg="#ffffff",fg="#173b46",relief="flat",borderwidth=0,highlightthickness=0,selectbackground="#d7f1ed",activestyle="none",yscrollcommand=scroll.set);display.pack(fill="both",expand=True,padx=8,pady=8);scroll.config(command=display.yview)
        comment_map={}
        def render(items):
            display.delete(0,"end");comment_map.clear()
            if not items:display.insert("end","Ainda não há comentários. Seja a primeira pessoa a comentar!")
            for item in items:
                display.insert("end",f'{item["author"]}  ·  {item["created_at"]}  |  {item["body"]}');comment_map[display.size()-1]=item
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
        def delete_comment():
            selection=display.curselection()
            if not selection or selection[0] not in comment_map:return
            comment=comment_map[selection[0]]
            if comment.get("author_id")!=self.client.state.get("user",{}).get("id"):
                messagebox.showinfo("Comentários","Só o autor pode apagar este comentário.",parent=window);return
            if not messagebox.askyesno("Apagar comentário","Remover este comentário?",parent=window):return
            def work():
                response=self.online("DELETE",f'/api/comments/{comment["id"]}');response.raise_for_status();self.after(0,lambda:(self.load_posts(),refresh_comments()))
            threading.Thread(target=lambda:self.handle(work),daemon=True).start()
        ttk.Button(composer,text="Apagar meu comentário",command=delete_comment).pack(side="right",fill="y");ttk.Button(composer,text="Enviar",command=send_comment).pack(side="right",fill="y",padx=(0,8))
    def publish_dialog(self):
        messagebox.showinfo("Publicar jogo","A API recebe pacote ZIP com bloom.json. Para reduzir risco, prepare o pacote fora do BLOOM, escaneie-o e leia a documentação. A publicação exige login.")
        path=filedialog.askopenfilename(filetypes=[("Pacote ZIP","*.zip")],parent=self)
        if not path:return
        name=simpledialog.askstring("Metadados","Nome do jogo:",parent=self);version=simpledialog.askstring("Metadados","Versão:",initialvalue="1.0.0",parent=self);fmt=simpledialog.askstring("Metadados","Formato: exe / pygame / bloom",parent=self)
        if not name or not version or fmt not in {"exe","pygame","bloom"}:messagebox.showerror("BLOOM","Metadados inválidos.");return
        cover=filedialog.askopenfilename(title="Capa opcional do projeto",filetypes=[("Imagens","*.png *.jpg *.jpeg *.webp *.gif")],parent=self)
        self.handle(lambda:self._publish(path,name,version,fmt,cover))
    def _publish(self,path,name,version,fmt,cover_path=""):
        with open(path,"rb") as f:r=self.online("POST","/api/games",data={"name":name,"version":version,"description":"","format":fmt},files={"file":(Path(path).name,f,"application/zip")})
        r.raise_for_status();result=r.json()
        if cover_path and result.get("id"):
            with open(cover_path,"rb") as image:cover_response=self.online("PUT",f'/api/games/{result["id"]}/cover',files={"file":(Path(cover_path).name,image,"application/octet-stream")})
            cover_response.raise_for_status()
        messagebox.showinfo("Publicação",("Projeto enviado para revisão. Ele não aparecerá no catálogo até aprovação.\n" if result.get("status")=="pending_review" else "Projeto publicado.\n")+f'Verificação automática: {result.get("moderation_findings") or "sem alertas heurísticos"}.\n\nIsto não é antivírus nem revisão legal.');self.load_games()

if __name__=="__main__":BloomApp().mainloop()
