"""BLOOM WORLD API. Dados persistidos; use Postgres em produção."""
from datetime import datetime, timedelta, timezone
from pathlib import Path, PureWindowsPath
import hashlib, hmac, os, re, secrets, shutil, uuid, zipfile
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

Base.metadata.create_all(engine)
app = FastAPI(title="BLOOM WORLD", version="0.1.0", description="API da comunidade e loja BLOOM")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("BLOOM_CORS_ORIGINS", "*").split(","), allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)
class LoginIn(BaseModel):
    username: str
    password: str
class TextIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
class ReportIn(BaseModel):
    target_type: str = Field(pattern="^(post|game|user)$")
    target_id: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=1000)
class RatingIn(BaseModel):
    score: int = Field(ge=1, le=5)


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

@app.post("/api/auth/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): raise HTTPException(422, "E-mail inválido")
    if db.scalar(select(User).where((User.username == data.username) | (User.email == email))): raise HTTPException(409, "Nome de usuário ou e-mail já cadastrado")
    user = User(username=data.username, email=email, password_hash=PASSWORDS.hash(data.password))
    db.add(user); db.commit(); db.refresh(user)
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
    p=Post(author_id=user.id,body=data.body);db.add(p);db.commit();db.refresh(p);return {"id":p.id,"author":user.username,"body":p.body,"created_at":p.created_at,"likes":0,"comments":0}
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
    return [{"id":c.id,"author":db.get(User,c.author_id).username,"body":c.body,"created_at":c.created_at} for c in db.scalars(select(Comment).where(Comment.post_id==post_id).order_by(Comment.created_at.asc()))]
@app.post("/api/posts/{post_id}/comments",status_code=201)
def add_comment(post_id:int,data:TextIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    if not db.get(Post,post_id): raise HTTPException(404,"Publicação não encontrada")
    c=Comment(post_id=post_id,author_id=user.id,body=data.body[:2000]);db.add(c);db.commit();db.refresh(c);return {"id":c.id,"author":user.username,"body":c.body,"created_at":c.created_at}

@app.post("/api/reports",status_code=201)
def report(data:ReportIn,user:User=Depends(require_user),db:Session=Depends(get_db)):
    target={"post":Post,"game":Game,"user":User}[data.target_type]
    if not db.get(target,data.target_id): raise HTTPException(404,"Alvo não encontrado")
    r=Report(reporter_id=user.id,target_type=data.target_type,target_id=data.target_id,reason=data.reason);db.add(r);db.commit();db.refresh(r);return {"id":r.id,"status":r.status}

@app.get("/api/games")
def list_games(q:str="",category:str="",db:Session=Depends(get_db)):
    stmt=select(Game).order_by(Game.created_at.desc())
    if q.strip(): stmt=stmt.where((Game.name.ilike(f"%{q.strip()}%"))|(Game.description.ilike(f"%{q.strip()}%")))
    if category in {"exe","pygame","bloom"}: stmt=stmt.where(Game.format==category)
    games=db.scalars(stmt.limit(100)).all()
    return [{"id":g.id,"slug":g.slug,"name":g.name,"version":g.version,"description":g.description,"format":g.format,"developer":db.get(User,g.developer_id).username,"sha256":g.sha256,"size":g.size,"created_at":g.created_at,"rating":db.scalar(select(func.avg(Rating.score)).where(Rating.game_id==g.id))} for g in games]
@app.get("/api/games/{slug}")
def game_detail(slug:str,db:Session=Depends(get_db)):
    g=db.scalar(select(Game).where(Game.slug==slug))
    if not g: raise HTTPException(404,"Jogo não encontrado")
    return {"id":g.id,"slug":g.slug,"name":g.name,"version":g.version,"description":g.description,"format":g.format,"developer":db.get(User,g.developer_id).username,"sha256":g.sha256,"size":g.size,"created_at":g.created_at,"rating":db.scalar(select(func.avg(Rating.score)).where(Rating.game_id==g.id))}
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
    temp=UPLOAD_DIR/f"{uuid.uuid4().hex}.part"; digest=hashlib.sha256(); size=0
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
        except zipfile.BadZipFile: raise HTTPException(400,"Arquivo ZIP inválido")
        final_name=f"{slug}.zip"; final_path=UPLOAD_DIR/final_name;temp.replace(final_path)
        g=Game(slug=slug,name=name,version=version,description=description,format=format,developer_id=user.id,package_name=final_name,sha256=digest.hexdigest(),size=size)
        db.add(g);db.commit();db.refresh(g)
        return {"id":g.id,"slug":slug,"sha256":g.sha256,"status":"published"}
    except Exception:
        temp.unlink(missing_ok=True);raise
    finally: file.file.close()
@app.get("/api/games/{slug}/download")
def download_game(slug:str,db:Session=Depends(get_db)):
    from fastapi.responses import FileResponse
    g=db.scalar(select(Game).where(Game.slug==slug))
    if not g:raise HTTPException(404,"Jogo não encontrado")
    path=UPLOAD_DIR/g.package_name
    if not path.is_file():raise HTTPException(503,"Pacote indisponível")
    return FileResponse(path,media_type="application/zip",filename=f"{slug}.zip",headers={"X-Content-SHA256":g.sha256})
