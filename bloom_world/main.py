"""BLOOM WORLD API. Dados persistidos; use Postgres em produção."""
from datetime import datetime, timedelta, timezone
from pathlib import Path, PureWindowsPath
import hashlib, hmac, os, re, secrets, shutil, uuid, zipfile, subprocess
import json
from typing import Optional
import jwt
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, select, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from .database import Base, engine, get_db

APP_DIR = Path(os.getenv("BLOOM_DATA_DIR", "./bloom_data")).resolve()
UPLOAD_DIR = APP_DIR / "packages"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR = APP_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
TERMS_VERSION = "1.0"
MODERATOR_IDS = {int(x) for x in os.getenv("BLOOM_MODERATOR_USER_IDS", "").split(",") if x.strip().isdigit()}
JWT_SECRET = os.getenv("BLOOM_JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = secrets.token_urlsafe(48)
    print("WARNING: BLOOM_JWT_SECRET not set. Tokens will invalidate when this process restarts; configure a persistent secret in production.")
JWT_ALGORITHM = "HS256"
TOKEN_HOURS = int(os.getenv("BLOOM_TOKEN_HOURS", "24"))
PASSWORDS = PasswordHash.recommended()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    bio: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text, default="")
    format: Mapped[str] = mapped_column(String(16))
    developer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    package_name: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("game_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    score: Mapped[int] = mapped_column(Integer)

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), default="")
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ConversationMember(Base):
    __tablename__ = "conversation_members"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DirectPair(Base):
    __tablename__ = "direct_pairs"
    id: Mapped[int] = mapped_column(primary_key=True)
    pair_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), unique=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class AccountMedia(Base):
    __tablename__ = "account_media"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    avatar_path: Mapped[str] = mapped_column(String(255), default="")

class GameMedia(Base):
    __tablename__ = "game_media"
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), unique=True, index=True)
    cover_path: Mapped[str] = mapped_column(String(255), default="")

class TermsAcceptance(Base):
    __tablename__ = "terms_acceptances"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(30))
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ModerationReview(Base):
    __tablename__ = "moderation_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="approved")
    findings: Mapped[str] = mapped_column(Text, default="[]")
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)
app = FastAPI(title="BLOOM WORLD", version="0.1.0", description="API da comunidade e loja BLOOM")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("BLOOM_CORS_ORIGINS", "*").split(","), allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)
    accept_terms: bool = False
class LoginIn(BaseModel):
    username: str
    password: str
class TextIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
class ReportIn(BaseModel):
    target_type: str = Field(pattern="^(post|game|user|message)$")
    target_id: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=1000)
class RatingIn(BaseModel):
    score: int = Field(ge=1, le=5)
class TermsIn(BaseModel):
    accept: bool
class ConversationIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
class GroupIn(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    usernames: list[str] = Field(min_length=1, max_length=49)
class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
class ModerationDecisionIn(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
class ReportDecisionIn(BaseModel):
    status: str = Field(pattern="^(resolved|dismissed)$")

def scan_publication_text(text: str):
    """Heuristics only: flags suspicious phrases; never proves a file is safe or unlawful."""
    value = text.casefold()
    patterns = {
        "possible_piracy": r"\b(crack|keygen|warez|pirated|pirata|pirataria|cracked|serial key|rom download)\b",
        "adult_content": r"\b(porn|porno|xxx|explicit sex|hentai|nude|nudity|conte[uú]do sexual|pornografia)\b",
        "graphic_violence": r"\b(gore|dismember|decapitat|torture|snuff|graphic violence|gore gr[aá]fico|tortura|decapita)\b",
        "self_harm_or_death": r"\b(suicide|self.harm|real death|real murder|suic[ií]dio|automutila[cç][aã]o|morte real|assassinato real)\b",
    }
    findings = [key for key, pattern in patterns.items() if re.search(pattern, value)]
    return findings

def scan_archive_names(names):
    findings = []
    dangerous = {".exe", ".scr", ".com", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".lnk", ".msi", ".dll", ".sys"}
    for name in names:
        lower = name.casefold()
        if Path(lower).suffix in dangerous:
            findings.append("executable_or_script_in_archive")
        findings.extend(scan_publication_text(Path(lower).name))
    return sorted(set(findings))

def scan_with_clamav(path:Path):
    """Use ClamAV if installed; otherwise explicitly report that no antivirus ran."""
    executable=shutil.which("clamscan")
    if not executable:return "unavailable", []
    try:
        result=subprocess.run([executable,"--no-summary",str(path)],capture_output=True,text=True,timeout=90,check=False)
        if result.returncode==0:return "clean_by_clamav", []
        if result.returncode==1:return "threat_detected", ["antivirus_threat_detected"]
        return "error", ["antivirus_scan_error"]
    except (OSError,subprocess.TimeoutExpired):return "error", ["antivirus_scan_error"]


def user_out(user: User):
    return {"id": user.id, "username": user.username, "bio": user.bio, "created_at": user.created_at}
def make_token(user: User):
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user.id), "iat": now, "exp": now + timedelta(hours=TOKEN_HOURS)}, JWT_SECRET, algorithm=JWT_ALGORITHM)
def current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    # OAuth-free Bearer parsing keeps API usable by the desktop client.
    from fastapi import Request
    raise RuntimeError("dependency placeholder")

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer = HTTPBearer(auto_error=False)
def require_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    user = db.get(User, user_id)
    if not user: raise HTTPException(status_code=401, detail="Conta não encontrada")
    return user

@app.get("/health")
def health(): return {"status": "ok", "service": "BLOOM WORLD", "version": app.version}

TERMS_TEXT = """BLOOM — Termos de Uso e Regras da Comunidade (versão 1.0)

1. Elegibilidade e conta. Você deve ter idade suficiente para usar o serviço conforme as leis aplicáveis. Mantenha sua senha segura e não se passe por outra pessoa.
2. Conteúdo permitido. Publique somente conteúdo que você criou ou tem autorização para distribuir. Pirataria, cópias não autorizadas, pornografia, exploração sexual, conteúdo sexual envolvendo menores, ameaças, incentivo à violência real, gore extremo, exploração de morte real, malware, fraude, doxxing, assédio e conteúdo ilegal são proibidos.
3. Jogos e arquivos. Você é responsável por licenças, direitos autorais, segurança e descrição do que enviar. Não envie executáveis maliciosos. A triagem automática do BLOOM é limitada e não garante que arquivos estejam seguros ou que direitos tenham sido respeitados. Usuários devem verificar downloads com ferramentas de segurança próprias.
4. Moderação. Conteúdo pode ser sinalizado, ocultado, removido ou encaminhado para revisão humana. Relatos podem ser analisados por moderadores. Violações repetidas podem levar a restrições ou suspensão. O BLOOM não promete detectar todo conteúdo nocivo.
5. Privacidade e mensagens. Chats são acessíveis aos seus participantes e podem ser denunciados. Não envie dados pessoais sensíveis. Mensagens privadas não devem ser tratadas como canal criptografado de ponta a ponta.
6. Direitos e licenças. Você mantém os direitos do conteúdo que envia e concede ao BLOOM permissão limitada para armazenar, exibir e distribuir esse conteúdo conforme necessário para operar o serviço. Remova conteúdo quando não quiser mais disponibilizá-lo.
7. Disponibilidade e responsabilidade. O serviço pode mudar, ficar indisponível ou remover conteúdo por segurança, obrigações legais ou manutenção. Estes termos não substituem aconselhamento jurídico e precisam ser revisados por profissional antes de uma publicação comercial.
8. Contato e denúncias. Use os recursos de denúncia disponíveis no app. Para emergência ou risco imediato, contate os serviços locais competentes.

Ao criar conta ou continuar usando os recursos comunitários, você confirma que leu e aceita estes termos. Versão atual: 1.0."""

@app.get("/api/terms")
def get_terms(): return {"version": TERMS_VERSION, "text": TERMS_TEXT}

@app.post("/api/terms/accept")
def accept_terms(data: TermsIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if not data.accept: raise HTTPException(400, "É necessário aceitar os termos para continuar")
    acceptance = TermsAcceptance(user_id=user.id, version=TERMS_VERSION)
    db.add(acceptance); db.commit()
    return {"accepted": True, "version": TERMS_VERSION}

@app.post("/api/auth/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if not data.accept_terms: raise HTTPException(400, "Leia e aceite os termos de uso para criar uma conta")
    email = data.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): raise HTTPException(422, "E-mail inválido")
    if db.scalar(select(User).where((User.username == data.username) | (User.email == email))): raise HTTPException(409, "Nome de usuário ou e-mail já cadastrado")
    user = User(username=data.username, email=email, password_hash=PASSWORDS.hash(data.password))
    db.add(user); db.commit(); db.refresh(user)
    db.add(TermsAcceptance(user_id=user.id, version=TERMS_VERSION)); db.commit()
    return {"access_token": make_token(user), "token_type": "bearer", "user": user_out(user)}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.username) == data.username.lower()))
    if not user or not PASSWORDS.verify(data.password, user.password_hash): raise HTTPException(401, "Usuário ou senha incorretos")
    return {"access_token": make_token(user), "token_type": "bearer", "user": user_out(user)}

@app.get("/api/me")
def me(user: User = Depends(require_user)): return user_out(user)
@app.get("/api/users/search")
def search_users(q: str = "", db: Session = Depends(get_db)):
    if len(q.strip()) < 2: return []
    return [user_out(u) for u in db.scalars(select(User).where(User.username.ilike(f"%{q.strip()}%")).limit(30))]
@app.get("/api/users/{username}")
def public_profile(username: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.username) == username.lower()))
    if not user: raise HTTPException(404, "Perfil não encontrado")
    return user_out(user)
@app.put("/api/me/bio")
def update_bio(data: TextIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    user.bio = data.body[:500]; db.commit(); return user_out(user)

def save_image_upload(file:UploadFile):
    from PIL import Image, UnidentifiedImageError
    raw=file.file.read(5*1024*1024+1)
    if len(raw)>5*1024*1024: raise HTTPException(413,"Imagem excede o limite de 5 MB")
    try:
        from io import BytesIO
        image=Image.open(BytesIO(raw))
        if image.width>10000 or image.height>10000 or image.width*image.height>25000000:raise HTTPException(413,"Resolução da imagem excede o limite permitido")
        image.verify()
        fmt=(image.format or "").upper()
    except HTTPException: raise
    except Exception: raise HTTPException(415,"Arquivo não é uma imagem reconhecida")
    suffix={"PNG":".png","JPEG":".jpg","WEBP":".webp","GIF":".gif"}.get(fmt)
    if not suffix: raise HTTPException(415,"Use PNG, JPEG, WEBP ou GIF")
    name=uuid.uuid4().hex+suffix;(MEDIA_DIR/name).write_bytes(raw)
    return name

@app.put("/api/me/avatar")
def upload_avatar(file:UploadFile=File(...),user:User=Depends(require_user),db:Session=Depends(get_db)):
    name=save_image_upload(file)
    item=db.scalar(select(AccountMedia).where(AccountMedia.user_id==user.id))
    if item and item.avatar_path: (MEDIA_DIR/item.avatar_path).unlink(missing_ok=True)
    if item:item.avatar_path=name
    else:db.add(AccountMedia(user_id=user.id,avatar_path=name))
    db.commit();return {"url":f"/api/users/{user.username}/avatar"}

@app.get("/api/users/{username}/avatar")
def get_avatar(username:str,db:Session=Depends(get_db)):
    from fastapi.responses import FileResponse
    user=db.scalar(select(User).where(func.lower(User.username)==username.lower()))
    if not user: raise HTTPException(404,"Perfil não encontrado")
    item=db.scalar(select(AccountMedia).where(AccountMedia.user_id==user.id))
    if not item or not item.avatar_path: raise HTTPException(404,"Este perfil não tem foto")
    path=MEDIA_DIR/item.avatar_path
    if not path.is_file(): raise HTTPException(404,"Foto indisponível")
    return FileResponse(path)

@app.get("/api/posts")
def list_posts(db: Session = Depends(get_db), limit: int = 30, offset: int = 0):
    posts = db.scalars(select(Post).order_by(Post.created_at.desc()).offset(max(0, offset)).limit(min(max(limit, 1), 100))).all()
    result=[]
    for p in posts:
        author=db.get(User,p.author_id)
        result.append({"id":p.id,"author":author.username if author else "[removido]","author_id":p.author_id,"body":p.body,"created_at":p.created_at,"likes":db.scalar(select(func.count(Like.id)).where(Like.post_id==p.id)),"comments":db.scalar(select(func.count(Comment.id)).where(Comment.post_id==p.id))})
    return result
@app.post("/api/posts", status_code=201)
def create_post(data: TextIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    findings=scan_publication_text(data.body)
    if findings: raise HTTPException(422,{"detail":"Publicação sinalizada pelas regras da comunidade","findings":findings})
    p=Post(author_id=user.id,body=data.body);db.add(p);db.commit();db.refresh(p);return {"id":p.id,"author":user.username,"body":p.body,"created_at":p.created_at,"likes":0,"comments":0}
@app.delete("/api/posts/{post_id}", status_code=204)
def delete_post(post_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    post=db.get(Post,post_id)
    if not post: raise HTTPException(404,"Publicação não encontrada")
    if post.author_id != user.id: raise HTTPException(403,"Só o autor pode apagar esta publicação")
    db.query(Comment).filter(Comment.post_id==post_id).delete(synchronize_session=False)
    db.query(Like).filter(Like.post_id==post_id).delete(synchronize_session=False)
    db.delete(post);db.commit()
@app.post("/api/posts/{post_id}/like")
def like_post(post_id:int,user:User=Depends(require_user),db:Session=Depends(get_db)):
    if not db.get(Post,post_id): raise HTTPException(404,"Publicação não encontrada")
    like=db.scalar(select(Like).where(Like.post_id==post_id,Like.user_id==user.id))
    if like: db.delete(like); liked=False
    else: db.add(Like(post_id=post_id,user_id=user.id)); liked=True
    db.commit(); return {"liked":liked,"likes":db.scalar(select(func.count(Like.id)).where(Like.post_id==post_id))}
@app.get("/api/posts/{post_id}/comments")
def list_comments(post_id:int,db:Session=Depends(get_db)):
    if not db.get(Post,post_id): raise HTTPException(404,"Publicação não encontrada")
    return [{"id":c.id,"author":db.get(User,c.author_id).username,"author_id":c.author_id,"body":c.body,"created_at":c.created_at} for c in db.scalars(select(Comment).where(Comment.post_id==post_id).order_by(Comment.created_at.asc()))]
@app.post("/api/posts/{post_id}/comments",status_code=201)
def add_comment(post_id:int,data:TextIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    if not db.get(Post,post_id): raise HTTPException(404,"Publicação não encontrada")
    findings=scan_publication_text(data.body)
    if findings: raise HTTPException(422,{"detail":"Comentário sinalizado pelas regras da comunidade","findings":findings})
    c=Comment(post_id=post_id,author_id=user.id,body=data.body[:2000]);db.add(c);db.commit();db.refresh(c);return {"id":c.id,"author":user.username,"body":c.body,"created_at":c.created_at}
@app.delete("/api/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    comment=db.get(Comment,comment_id)
    if not comment: raise HTTPException(404,"Comentário não encontrado")
    if comment.author_id != user.id: raise HTTPException(403,"Só o autor pode apagar este comentário")
    db.delete(comment);db.commit()

def require_member(conversation_id: int, user: User, db: Session):
    member=db.scalar(select(ConversationMember).where(ConversationMember.conversation_id==conversation_id,ConversationMember.user_id==user.id))
    if not member: raise HTTPException(404,"Conversa não encontrada")
    return member

@app.get("/api/chats")
def list_chats(user: User=Depends(require_user),db: Session=Depends(get_db)):
    ids=db.scalars(select(ConversationMember.conversation_id).where(ConversationMember.user_id==user.id)).all()
    result=[]
    for cid in ids:
        conv=db.get(Conversation,cid)
        if not conv: continue
        members=db.scalars(select(ConversationMember).where(ConversationMember.conversation_id==cid)).all()
        users=[db.get(User,m.user_id) for m in members]
        last=db.scalar(select(ChatMessage).where(ChatMessage.conversation_id==cid).order_by(ChatMessage.created_at.desc()).limit(1))
        result.append({"id":cid,"title":conv.title,"is_group":conv.is_group,"members":[u.username for u in users if u],"last_message":last.body if last else "","created_at":conv.created_at})
    return result

@app.post("/api/chats/direct",status_code=201)
def create_direct_chat(data: ConversationIn,user: User=Depends(require_user),db: Session=Depends(get_db)):
    target=db.scalar(select(User).where(func.lower(User.username)==data.username.lower()))
    if not target: raise HTTPException(404,"Usuário não encontrado")
    if target.id==user.id: raise HTTPException(400,"Não é possível iniciar um chat consigo mesmo")
    pair_key=f"{min(user.id,target.id)}:{max(user.id,target.id)}"
    existing=db.scalar(select(DirectPair).where(DirectPair.pair_key==pair_key))
    if existing: return {"id":existing.conversation_id,"created":False}
    conv=Conversation(title=target.username,is_group=False,created_by=user.id);db.add(conv);db.flush()
    db.add_all([ConversationMember(conversation_id=conv.id,user_id=user.id),ConversationMember(conversation_id=conv.id,user_id=target.id)])
    db.add(DirectPair(pair_key=pair_key,conversation_id=conv.id));db.commit()
    return {"id":conv.id,"created":True}

@app.post("/api/chats/groups",status_code=201)
def create_group(data: GroupIn,user: User=Depends(require_user),db: Session=Depends(get_db)):
    names=list(dict.fromkeys([user.username]+data.usernames))
    if len(names)<3: raise HTTPException(422,"Um grupo precisa de pelo menos 3 participantes, incluindo você")
    users=db.scalars(select(User).where(func.lower(User.username).in_([n.lower() for n in names]))).all()
    by_name={u.username.lower():u for u in users}
    missing=[n for n in names if n.lower() not in by_name]
    if missing: raise HTTPException(404,"Usuário(s) não encontrado(s): "+", ".join(missing))
    conv=Conversation(title=data.title.strip(),is_group=True,created_by=user.id);db.add(conv);db.flush()
    db.add_all([ConversationMember(conversation_id=conv.id,user_id=by_name[n.lower()].id) for n in names]);db.commit()
    return {"id":conv.id,"title":conv.title,"members":names}

@app.get("/api/chats/{conversation_id}/messages")
def list_messages(conversation_id:int,limit:int=100,user:User=Depends(require_user),db:Session=Depends(get_db)):
    require_member(conversation_id,user,db)
    rows=db.scalars(select(ChatMessage).where(ChatMessage.conversation_id==conversation_id).order_by(ChatMessage.created_at.desc()).limit(min(max(limit,1),200))).all()
    return [{"id":m.id,"sender":db.get(User,m.sender_id).username,"sender_id":m.sender_id,"body":m.body,"created_at":m.created_at} for m in reversed(rows)]

@app.post("/api/chats/{conversation_id}/messages",status_code=201)
def send_message(conversation_id:int,data:MessageIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    require_member(conversation_id,user,db)
    findings=scan_publication_text(data.body)
    if findings: raise HTTPException(422,{"detail":"Mensagem sinalizada pela regra de conteúdo da comunidade","findings":findings})
    msg=ChatMessage(conversation_id=conversation_id,sender_id=user.id,body=data.body.strip());db.add(msg);db.commit();db.refresh(msg)
    return {"id":msg.id,"sender":user.username,"sender_id":user.id,"body":msg.body,"created_at":msg.created_at}

@app.delete("/api/chats/{conversation_id}/messages/{message_id}",status_code=204)
def delete_message(conversation_id:int,message_id:int,user:User=Depends(require_user),db:Session=Depends(get_db)):
    require_member(conversation_id,user,db)
    msg=db.get(ChatMessage,message_id)
    if not msg or msg.conversation_id!=conversation_id: raise HTTPException(404,"Mensagem não encontrada")
    if msg.sender_id!=user.id: raise HTTPException(403,"Só quem enviou pode apagar esta mensagem")
    db.delete(msg);db.commit()

@app.post("/api/reports",status_code=201)
def report(data:ReportIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    target={"post":Post,"game":Game,"user":User,"message":ChatMessage}[data.target_type]
    if not db.get(target,data.target_id): raise HTTPException(404,"Alvo não encontrado")
    r=Report(reporter_id=user.id,target_type=data.target_type,target_id=data.target_id,reason=data.reason);db.add(r);db.commit();db.refresh(r);return {"id":r.id,"status":r.status}

@app.get("/api/games")
def list_games(q:str="",category:str="",db:Session=Depends(get_db)):
    stmt=select(Game).outerjoin(ModerationReview,ModerationReview.game_id==Game.id).where((ModerationReview.status==None)|(ModerationReview.status=="approved")).order_by(Game.created_at.desc())
    if q.strip(): stmt=stmt.where((Game.name.ilike(f"%{q.strip()}%"))|(Game.description.ilike(f"%{q.strip()}%")))
    if category in {"exe","pygame","bloom"}: stmt=stmt.where(Game.format==category)
    games=db.scalars(stmt.limit(100)).all()
    return [{"id":g.id,"slug":g.slug,"name":g.name,"version":g.version,"description":g.description,"format":g.format,"developer":db.get(User,g.developer_id).username,"developer_id":g.developer_id,"cover_url":f"/api/games/{g.id}/cover" if db.scalar(select(GameMedia).where(GameMedia.game_id==g.id)) else None,"sha256":g.sha256,"size":g.size,"created_at":g.created_at,"rating":db.scalar(select(func.avg(Rating.score)).where(Rating.game_id==g.id))} for g in games]
@app.get("/api/games/{slug}")
def game_detail(slug:str,db:Session=Depends(get_db)):
    g=db.scalar(select(Game).where(Game.slug==slug))
    if not g: raise HTTPException(404,"Jogo não encontrado")
    review=db.scalar(select(ModerationReview).where(ModerationReview.game_id==g.id))
    if review and review.status!="approved": raise HTTPException(404,"Jogo não encontrado")
    return {"id":g.id,"slug":g.slug,"name":g.name,"version":g.version,"description":g.description,"format":g.format,"developer":db.get(User,g.developer_id).username,"sha256":g.sha256,"size":g.size,"cover_url":f"/api/games/{g.id}/cover" if db.scalar(select(GameMedia).where(GameMedia.game_id==g.id)) else None,"created_at":g.created_at,"rating":db.scalar(select(func.avg(Rating.score)).where(Rating.game_id==g.id))}

@app.put("/api/games/{game_id}/cover")
def upload_game_cover(game_id:int,file:UploadFile=File(...),user:User=Depends(require_user),db:Session=Depends(get_db)):
    game=db.get(Game,game_id)
    if not game: raise HTTPException(404,"Projeto não encontrado")
    if game.developer_id!=user.id: raise HTTPException(403,"Só o autor pode editar a capa")
    name=save_image_upload(file)
    item=db.scalar(select(GameMedia).where(GameMedia.game_id==game_id))
    if item and item.cover_path: (MEDIA_DIR/item.cover_path).unlink(missing_ok=True)
    if item:item.cover_path=name
    else:db.add(GameMedia(game_id=game_id,cover_path=name))
    db.commit();return {"url":f"/api/games/{game_id}/cover"}

@app.get("/api/games/{game_id}/cover")
def get_game_cover(game_id:int,db:Session=Depends(get_db)):
    from fastapi.responses import FileResponse
    item=db.scalar(select(GameMedia).where(GameMedia.game_id==game_id))
    if not item or not item.cover_path: raise HTTPException(404,"Projeto sem capa")
    path=MEDIA_DIR/item.cover_path
    if not path.is_file(): raise HTTPException(404,"Capa indisponível")
    return FileResponse(path)

@app.post("/api/games/{game_id}/rating")
def rate_game(game_id:int,data:RatingIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    if not db.get(Game,game_id): raise HTTPException(404,"Jogo não encontrado")
    r=db.scalar(select(Rating).where(Rating.game_id==game_id,Rating.user_id==user.id))
    if r:r.score=data.score
    else:db.add(Rating(game_id=game_id,user_id=user.id,score=data.score))
    db.commit();return {"average":db.scalar(select(func.avg(Rating.score)).where(Rating.game_id==game_id))}

def allowed_archive(file: UploadFile):
    suffix=Path(file.filename or "").suffix.lower()
    if suffix not in {".zip"}: raise HTTPException(415,"Envie um pacote ZIP contendo o jogo e bloom.json. Pacotes avulsos ainda não são aceitos pela API.")
    return suffix
@app.post("/api/games",status_code=201)
def publish_game(name:str=Form(...),version:str=Form(...),description:str=Form(""),format:str=Form(...),file:UploadFile=File(...),user:User=Depends(require_user),db:Session=Depends(get_db)):
    if format not in {"exe","pygame","bloom"}: raise HTTPException(422,"Formatos permitidos: exe, pygame, bloom")
    allowed_archive(file)
    if len(name)>100 or len(version)>40 or len(description)>10000: raise HTTPException(422,"Metadados excedem os limites")
    slug=f"{re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')[:50] or 'jogo'}-{uuid.uuid4().hex[:8]}"
    temp=UPLOAD_DIR/f"{uuid.uuid4().hex}.part"; digest=hashlib.sha256(); size=0;archive_findings=[]
    try:
        with temp.open("wb") as out:
            while chunk:=file.file.read(1024*1024):
                size+=len(chunk)
                if size>300*1024*1024: raise HTTPException(413,"Pacote excede 300 MB")
                digest.update(chunk);out.write(chunk)
        try:
            with zipfile.ZipFile(temp) as z:
                names=z.namelist()
                if any(Path(n.replace("\\", "/")).is_absolute() or PureWindowsPath(n).is_absolute() or PureWindowsPath(n).drive or ".." in n.replace("\\", "/").split("/") for n in names): raise HTTPException(400,"ZIP contém caminho inseguro")
                manifests=[n for n in names if Path(n).name.lower()=="bloom.json"]
                if not manifests: raise HTTPException(400,"O pacote precisa incluir bloom.json")
                if len(names)>10000 or sum(i.file_size for i in z.infolist())>1024*1024*1024: raise HTTPException(413,"Conteúdo descompactado excede os limites")
                import json
                manifest=json.loads(z.read(manifests[0]))
                for key in ("name","version","developer","description","format","files"):
                    if key not in manifest: raise HTTPException(400,f"Manifesto incompleto: falta {key}")
                if manifest["format"]!=format: raise HTTPException(400,"Formato do manifesto não corresponde ao informado")
                archive_findings=scan_archive_names(names)
                for info in z.infolist():
                    if Path(info.filename).suffix.lower() in {".txt",".md",".html",".json",".xml"} and info.file_size<=256*1024:
                        try:archive_findings.extend(scan_publication_text(z.read(info).decode("utf-8",errors="ignore")))
                        except Exception:pass
        except zipfile.BadZipFile: raise HTTPException(400,"Arquivo ZIP inválido")
        final_name=f"{slug}.zip"; final_path=UPLOAD_DIR/final_name;temp.replace(final_path)
        review_text=" ".join([name,version,description,manifest.get("name", ""),manifest.get("description", "")])
        findings=scan_publication_text(review_text)+archive_findings
        findings=sorted(set(findings))
        antivirus_status,antivirus_findings=scan_with_clamav(final_path)
        findings=sorted(set(findings+antivirus_findings))
        review_status="pending" if findings else "approved"
        g=Game(slug=slug,name=name,version=version,description=description,format=format,developer_id=user.id,package_name=final_name,sha256=digest.hexdigest(),size=size)
        db.add(g);db.flush();db.add(ModerationReview(game_id=g.id,status=review_status,findings=json.dumps(findings)));db.commit();db.refresh(g)
        return {"id":g.id,"slug":slug,"sha256":g.sha256,"status":"pending_review" if findings else "published","moderation_findings":findings,"antivirus_status":antivirus_status,"moderation_disclaimer":"Triagem automática limitada; um resultado limpo do ClamAV não é garantia de segurança nem verificação legal."}
    except Exception:
        temp.unlink(missing_ok=True);raise
    finally: file.file.close()
@app.get("/api/games/{slug}/download")
def download_game(slug:str,db:Session=Depends(get_db)):
    from fastapi.responses import FileResponse
    g=db.scalar(select(Game).where(Game.slug==slug))
    if not g:raise HTTPException(404,"Jogo não encontrado")
    review=db.scalar(select(ModerationReview).where(ModerationReview.game_id==g.id))
    if review and review.status!="approved": raise HTTPException(404,"Jogo não encontrado")
    path=UPLOAD_DIR/g.package_name
    if not path.is_file():raise HTTPException(503,"Pacote indisponível")
    return FileResponse(path,media_type="application/zip",filename=f"{slug}.zip",headers={"X-Content-SHA256":g.sha256})

@app.delete("/api/games/{game_id}",status_code=204)
def delete_game(game_id:int,user:User=Depends(require_user),db:Session=Depends(get_db)):
    game=db.get(Game,game_id)
    if not game: raise HTTPException(404,"Projeto não encontrado")
    if game.developer_id!=user.id and user.id not in MODERATOR_IDS: raise HTTPException(403,"Só o autor pode remover este projeto")
    (UPLOAD_DIR/game.package_name).unlink(missing_ok=True)
    media=db.scalar(select(GameMedia).where(GameMedia.game_id==game_id))
    if media and media.cover_path:(MEDIA_DIR/media.cover_path).unlink(missing_ok=True)
    if media:db.delete(media)
    review=db.scalar(select(ModerationReview).where(ModerationReview.game_id==game_id))
    if review:db.delete(review)
    db.delete(game);db.commit()

def require_moderator(user:User):
    if user.id not in MODERATOR_IDS: raise HTTPException(403,"Acesso restrito a moderadores configurados")
    return user

@app.get("/api/moderation/queue")
def moderation_queue(user:User=Depends(require_user),db:Session=Depends(get_db)):
    require_moderator(user)
    rows=db.scalars(select(ModerationReview).where(ModerationReview.status=="pending").order_by(ModerationReview.scanned_at.asc())).all()
    out=[]
    for row in rows:
        g=db.get(Game,row.game_id)
        if g: out.append({"game_id":g.id,"name":g.name,"developer":db.get(User,g.developer_id).username,"findings":json.loads(row.findings),"created_at":g.created_at})
    return out

@app.post("/api/moderation/games/{game_id}")
def decide_moderation(game_id:int,data:ModerationDecisionIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    require_moderator(user)
    row=db.scalar(select(ModerationReview).where(ModerationReview.game_id==game_id))
    if not row: raise HTTPException(404,"Revisão não encontrada")
    row.status=data.status;db.commit();return {"game_id":game_id,"status":row.status}

@app.get("/api/moderation/reports")
def moderation_reports(user:User=Depends(require_user),db:Session=Depends(get_db)):
    require_moderator(user)
    rows=db.scalars(select(Report).where(Report.status=="open").order_by(Report.created_at.asc())).all()
    return [{"id":r.id,"reporter":db.get(User,r.reporter_id).username,"target_type":r.target_type,"target_id":r.target_id,"reason":r.reason,"created_at":r.created_at} for r in rows]

@app.post("/api/moderation/reports/{report_id}")
def decide_report(report_id:int,data:ReportDecisionIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    require_moderator(user)
    report=db.get(Report,report_id)
    if not report:raise HTTPException(404,"Denúncia não encontrada")
    report.status=data.status;db.commit();return {"id":report.id,"status":report.status}
