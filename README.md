# BLOOM — plataforma de jogos, comunidade e criação

**A world full of possibilities.** Esta entrega é uma primeira versão funcional do código-fonte: cliente desktop Python/Tkinter, API remota FastAPI, catálogo comunitário com pacotes ZIP, comunidade persistente, BLOOM MAKER visual básico e verificações locais BLOOM SAFE. O desktop e a API são serviços separados. Nenhum servidor é iniciado dentro do executável.

> **Estado honesto:** o código suporta Postgres e armazenamento externo Supabase, mas a API ainda precisa ser implantada e configurada com segredos antes de atender jogadores. Não foi gerado um executável Windows nesta máquina Linux. A triagem de segurança é limitada; não existe antivírus comercial nem sandbox de execução do Windows. A API não usa localhost por padrão; use localhost apenas para desenvolvimento deliberado. A plataforma nunca inicia um jogo automaticamente.

## Conteúdo

- `bloom_app/`: cliente desktop, loja, feed, biblioteca, perfis, chats e configurações multilíngues.
- `bloom_world/`: API FastAPI, persistência SQLAlchemy e endpoints para contas, termos, posts, comentários, chats, denúncias, catálogo, moderação e downloads.
- `bloom_maker/`: protótipo de editor visual de cenas 2D com eventos/blocos, objetos, imagem, áudio, salvamento e exportação ZIP.
- `bloom_safe/`: hash SHA-256, inspeção básica de ZIP, indicadores de risco e ressalva explícita de que isso não é antivírus.
- `assets/bloom.json.example`: modelo de manifesto; `assets/bloom.ico`: ícone original.
- `tests/`: verificações automatizadas.
- `Dockerfile`: imagem para hospedar só a API.

## O que funciona nesta versão

- Cadastro de contas com hash Argon2, login e token JWT; busca e perfil público.
- Publicações, comentários e mensagens com exclusão pelo autor, curtidas, avaliações, chats privados/grupos e denúncias persistidos no banco.
- Catálogo pesquisável por nome/formato; publicação de jogos autenticada como ZIP com `bloom.json`; download remoto, validação de SHA-256, instalação com verificação de caminhos e desinstalação.
- Formatos aceitos pela API: `exe`, `pygame` e `bloom`. A versão atual recebe pacotes ZIP; o conteúdo do formato é responsabilidade do desenvolvedor e não é automaticamente executado. Manifesto exemplo em `assets/bloom.json.example`.
- Arquivos de usuário podem ficar localmente em `BLOOM_DATA_DIR` ou em bucket privado Supabase Storage quando `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estão configurados. Em Supabase Free, cada arquivo é limitado no BLOOM a 45 MB; o armazenamento total incluído é limitado e o projeto pode pausar por inatividade.
- BLOOM MAKER salva/abre JSON e exporta ZIP com imagem/áudio e blocos 2D básicos; sua prévia é protótipo, não runtime distribuível.
- BLOOM SAFE e API fazem triagem de hash/ZIP/caminhos/texto/extensões; ClamAV é opcional no servidor. Nada disso garante segurança, legalidade nem análise visual.
- A pasta de dados do desktop fica em `%APPDATA%\BLOOM`, fora da pasta temporária do PyInstaller.

## Ainda pendente / limites de segurança

1. **BLOOM MAKER**: 3D, runtime jogável standalone, sistema de cenas múltiplas, colisões, física, animações e exportador executável ainda não estão implementados. A prévia executa um conjunto pequeno de blocos 2D.
2. **Arquivos `.py`**: a API deixa registrar `pygame`, mas não verifica por completo se são Pygame. Executá-los dentro de um app PyInstaller não está implementado; não se promete execução portátil desses scripts.
3. **Segurança**: moderação por palavras/nome e antivírus ClamAV opcional são incompletos; não há detecção visual, garantia antivírus, sandbox de processos, assinatura de publicador, rate limiting avançado, recuperação de senha ou 2FA. Projetos sinalizados exigem moderador configurado. Chats não têm criptografia ponta a ponta.
4. **Loja**: upload é ZIP até 300 MB no modo local e até 45 MB no modo cloud configurado com o bucket gratuito do Supabase; capa opcional. Categorias, instalador/atualizador delta e compras não estão implementados. Faça backup antes de atualizar.
5. **Perfis/idiomas**: avatar opcional e seletor com 12 idiomas estão disponíveis em escopo inicial; parte de mensagens/termos ainda pode estar em português/inglês. Favoritos, histórico e notificações não estão implementados.
6. **Produção**: configurar Postgres gerenciado, segredo JWT fixo, TLS, backups do banco e dos pacotes, monitoramento/alertas e política de moderação. A API cria tabelas com `create_all` para facilitar a primeira inicialização, mas não possui migrações Alembic.
7. **Disponibilidade**: Docker `restart: unless-stopped` reinicia o processo; disponibilidade 24/7 depende do provedor, plano sempre ativo, monitoramento e backups. O plano gratuito de alguns hosts pode suspender serviços. Não há SLA configurado.
8. **Cliente**: interface Tkinter funcional, mas não foi testada visualmente neste ambiente Linux sem desktop. Requer Windows com suporte gráfico. PyInstaller e arquivo `.exe` precisam ser produzidos/testados no Windows.

## Instalação no Windows 10/11 (PowerShell)

1. Instale Python 3.12 de [python.org](https://www.python.org/downloads/windows/) e marque **Add python.exe to PATH**. Git é opcional. Abra novo PowerShell e confira:

```powershell
py -3.12 --version
py -3.12 -m pip --version
```

2. Descompacte/clonar o projeto em um diretório sem sincronização/ACL restritiva, por exemplo `C:\BLOOM`. Abra PowerShell nessa raiz (onde está `requirements.txt`):

```powershell
cd C:\BLOOM
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se a política bloquear ativação, não é preciso alterar política: rode os comandos usando o caminho direto:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Rode a API de desenvolvimento em um terminal PowerShell, a partir da raiz:

```powershell
$env:BLOOM_JWT_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(48))")
$env:BLOOM_DATA_DIR = "$PWD\dev_bloom_data"
python -m uvicorn bloom_world.main:app --host 127.0.0.1 --port 8000 --reload
```

Acesse `http://127.0.0.1:8000/docs` no navegador para explorar a documentação interativa e `http://127.0.0.1:8000/health` para checar saúde. Esse modo é **somente desenvolvimento local**. `dev_bloom_data` guarda pacotes; o banco SQLite `bloom_world.db` é criado no diretório corrente.

4. Em outro PowerShell, cliente desktop:

```powershell
cd C:\BLOOM
.\.venv\Scripts\Activate.ps1
python -m bloom_app.main
```

Abra Configurações, defina `http://127.0.0.1:8000` (apenas no mesmo PC de desenvolvimento) e pressione **Salvar URL** / **Testar conexão**. Cadastre usuário na aba Perfil. Para testar em dois computadores, substitua localhost por uma URL pública HTTPS conforme a seção de implantação; `127.0.0.1` no segundo PC aponta para o próprio segundo PC, não para o servidor.

5. Rode os testes na raiz do repositório:

```powershell
python -m pytest -q
python -m compileall -q bloom_app bloom_world bloom_safe bloom_maker tests
```

## Configurar PostgreSQL e desenvolver com ele

Instale PostgreSQL localmente ou use um banco gerenciado. Crie um banco e usuário dedicados, não use superusuário. No PowerShell (substitua valores; mantenha a senha só em segredo local):

```powershell
$env:BLOOM_DATABASE_URL = "postgresql+psycopg://bloom_user:SENHA@127.0.0.1:5432/bloom"
$env:BLOOM_JWT_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(48))")
python -m uvicorn bloom_world.main:app --host 127.0.0.1 --port 8000
```

No serviço publicado, insira `BLOOM_DATABASE_URL` no cofre de variáveis do provedor. O código aceita connection strings `postgres://`, `postgresql://` e `postgresql+psycopg://`. Não comite `.env`, senhas, tokens nem uma URL de banco com credenciais. `BLOOM_JWT_SECRET` precisa ser aleatório, persistente e igual após reinícios; trocá-lo invalida sessões existentes. Com object storage configurado, os ZIPs e imagens não dependem de `BLOOM_DATA_DIR` após o upload.

## Primeira hospedagem sem custo: Render + Supabase

O Supabase Free fornece Postgres (500 MB), 1 GB de arquivos e 5 GB de tráfego de saída, mas pode pausar projetos com pouca atividade por sete dias e não inclui backups baixáveis do banco. O Render Free suspende o processo web após inatividade, pode demorar para acordar e não mantém arquivos do container nem volumes persistentes. Portanto, esta configuração serve para teste e uma primeira versão pequena, não para disponibilidade 24/7, SLA ou dados críticos. Não ative plano pago, teste ou método de pagamento para seguir este guia.

1. Crie no Supabase uma organização no plano **Free ($0)** e um projeto Postgres. Na página **Storage > Files > Buckets**, crie `bloom-assets` como bucket **privado**. O código limita pacotes a 45 MB quando usa esse armazenamento gratuito. Copie a URL do projeto, a connection string PostgreSQL e uma chave secreta de servidor; nunca use a chave pública no servidor.
2. No Render, crie um **Web Service** conectado ao repositório GitHub `zyxzxm/bloom`. Use o `Dockerfile` do repositório, instância **Free**, e não adicione disco persistente nem banco Render (o banco Render Free expira). Se o painel exigir cartão, plano pago ou teste, cancele sem concluir.
3. No painel **Environment** do serviço, cadastre `BLOOM_DATABASE_URL` (connection string Postgres do Supabase), `SUPABASE_URL` (URL do projeto), `SUPABASE_SERVICE_ROLE_KEY` (chave secreta do servidor) e `SUPABASE_STORAGE_BUCKET=bloom-assets`. O Blueprint gera e mantém `BLOOM_JWT_SECRET` automaticamente. Cadastre os segredos somente no painel privado do Render. Não os cole em GitHub, README, chat ou arquivo `.env` comitado.
4. Aguarde o build e o deploy; teste `https://SEU-SERVICO.onrender.com/health`. Essa URL HTTPS é a que o instalador Windows deve receber como endereço da API. Faça primeiro cadastro e publicação de um ZIP de teste com menos de 45 MB.
5. Verifique diariamente a tela de uso do Supabase. O plano Free pode pausar após inatividade e tem cotas de banco, arquivos e tráfego; a API pode acordar lentamente no Render Free. Exporte cópias do banco/arquivos por conta própria antes de guardar conteúdo importante. Para uma comunidade pública confiável, planeje um host sempre ativo e backups, que podem ter custo.

Em uma instância Render Free, use `https://...onrender.com` como URL pública; configure `BLOOM_CORS_ORIGINS` apenas se uma origem web específica for necessária. O cliente desktop chama diretamente a API e não depende de CORS do navegador.

## Implantar a API em uma VM Linux na nuvem

O computador do desenvolvedor não hospeda o serviço. Contrate uma VM/servidor sempre ativo com Docker, endereço público, domínio e TLS (ou proxy gerenciado). Configure firewall para expor somente SSH restrito e HTTPS; não exponha Postgres à internet. Um reverse proxy Caddy/Nginx ou proxy TLS do provedor deve encaminhar HTTPS ao container. O exemplo abaixo executa a API separadamente do cliente e reinicia o container após falha/reboot.

1. Faça checkout/cópia do diretório `bloom` na VM. Instale Docker Engine e o plugin Compose seguindo o guia oficial da distribuição Linux/provedor. Configure DNS `api.seudominio.tld` para o endereço da VM e TLS no proxy. Não publique a aplicação em HTTP aberto.
2. Na raiz, crie `compose.yaml`:

```yaml
services:
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: bloom
      POSTGRES_USER: bloom
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?defina POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bloom -d bloom"]
      interval: 10s
      timeout: 5s
      retries: 10
  api:
    build: .
    restart: unless-stopped
    environment:
      BLOOM_DATABASE_URL: postgresql+psycopg://bloom:${POSTGRES_PASSWORD}@db:5432/bloom
      BLOOM_JWT_SECRET: ${BLOOM_JWT_SECRET:?defina BLOOM_JWT_SECRET}
      BLOOM_DATA_DIR: /data
      BLOOM_CORS_ORIGINS: https://seudominio.tld
      BLOOM_MODERATOR_USER_IDS: ${BLOOM_MODERATOR_USER_IDS:-}
    volumes:
      - bloom_packages:/data
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "127.0.0.1:8000:8000"
volumes:
  postgres_data:
  bloom_packages:
```

3. Crie `.env` no servidor (permissão privada, nunca envie para Git):

```bash
umask 077
printf 'POSTGRES_PASSWORD=%s\nBLOOM_JWT_SECRET=%s\n' "$(openssl rand -hex 32)" "$(openssl rand -hex 48)" > .env
printf 'BLOOM_MODERATOR_USER_IDS=\n' >> .env
```

4. Suba e confira. Um proxy TLS deve encaminhar a porta interna 8000 do serviço `api`:

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 api
curl -fsS http://127.0.0.1:8000/health
```

O `curl` local serve só para diagnóstico na VM. A URL dos clientes é o host público HTTPS do proxy, por exemplo `https://api.seudominio.tld`; não use localhost. Configure essa URL em Configurações no BLOOM instalado em cada PC. Faça um teste em dois computadores diferentes: crie contas diferentes, publique post no primeiro e atualize feed no segundo; publique um ZIP de teste e baixe no segundo. Não use jogos desconhecidos para teste.

5. Disponibilidade e operação: habilite reinicialização automática da VM, monitor externo de `/health`, alertas de indisponibilidade/disco, atualizações de segurança e backups fora da VM. Teste restauração de Postgres **e** dos pacotes. O Compose reinicia containers, não substitui monitoramento/backup. Se usar hospedagem PaaS em vez de VM, verifique suspensão por inatividade, volume persistente, limites de upload, conexão Postgres e retenção de dados do plano antes de escolher.

## Distribuir jogo aceito

Prepare um diretório com `bloom.json` (renomeie `assets/bloom.json.example`), os arquivos listados e compacte **o conteúdo** em ZIP, de modo que o manifesto esteja dentro do ZIP. Exemplo de manifesto:

```json
{
  "name": "Jardim de Teste",
  "version": "1.0.0",
  "developer": "seu_usuario",
  "description": "Pacote experimental",
  "format": "bloom",
  "files": ["scene.bloom.json"],
  "entrypoint": "scene.bloom.json"
}
```

`format` deve corresponder ao formato selecionado (`exe`, `pygame` ou `bloom`). Entre em conta, use **Publicar pacote ZIP** em Garden e forneça nome/versão/formato. Verifique cuidadosamente qualquer binário antes de distribuí-lo. O cliente faz hash e extrai com verificação de caminho; **não executa o conteúdo**. O BLOOM MAKER agora pode exportar projeto 2D com blocos para ZIP e pré-visualizar eventos básicos; ainda não é um runtime de jogo standalone.

## Abrir BLOOM MAKER

Na tela inicial, clique no cartão BLOOM MAKER. Crie objetos retangulares/elípticos, arraste no canvas, importe imagens e áudios, adicione blocos ligados a eventos “Ao iniciar” e “Ao clicar”, salve/abra `.bloom.json`, exporte um ZIP com `bloom.json` e teste uma prévia 2D interativa. Os blocos implementados incluem movimento, texto, cor e reprodução de áudio. Trata-se de uma engine/protótipo 2D inicial; não há ainda física, colisão, animação avançada ou runtime standalone para os jogos baixados. A engine 3D fica para uma atualização futura.

## Compilar e publicar para jogadores

O fluxo de distribuição foi simplificado. No PC do desenvolvedor (Windows), instale Python 3.12 e Inno Setup 6, abra PowerShell na pasta do projeto e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

O script instala as ferramentas de build no ambiente local, pede a URL HTTPS pública da API, verifica `/health` e gera `release\BLOOM-Setup.exe`. **Python é necessário apenas no PC que compila.** O jogador recebe o instalador e não precisa instalar Python, abrir terminal nem ajustar URL. O instalador cria atalho, instala por usuário e permite desinstalar.

Leia o guia curto [PUBLICAR.md](PUBLICAR.md) para as etapas exatas. Para segurança, teste o instalador em Windows 10/11 limpo antes de publicar. O servidor FastAPI permanece separado; ele precisa estar implantado numa nuvem antes do build, pois o cliente precisa da URL real. Nunca distribua apontando para localhost ou URL de exemplo. O `.exe` de Windows não pode ser compilado neste ambiente Linux; rode o script num PC Windows.

## Atualizar aplicativo/backend sem perder dados

**Cliente:** mantenha backup de `%APPDATA%\BLOOM` se precisar preservar estado local. Compile novo executável e distribua nova versão. O arquivo pode ser substituído após fechar BLOOM. Banco e contas residem no servidor, não no EXE.

**API:** faça backup consistente do Postgres e volume de pacotes antes de atualizar:

```bash
docker compose exec -T db pg_dump -U bloom bloom > backup-antes.sql
docker run --rm -v bloom_bloom_packages:/data -v "$PWD:/backup" alpine tar czf /backup/pacotes-antes.tar.gz -C /data .
```

Confirme os nomes dos volumes com `docker volume ls` (prefixo deriva do nome do projeto Compose). Depois atualize código e recrie apenas API:

```bash
git pull --ff-only
docker compose build api
docker compose up -d --no-deps api
docker compose logs --tail=100 api
curl -fsS https://api.seudominio.tld/health
```

Não use `docker compose down -v`: remove volumes e pode apagar banco/arquivos. Não há migrações de esquema automatizadas nessa versão; alterações incompatíveis de modelo exigem plano de migração e cópia restaurável. Teste uma restauração antes de atualização de dados importante.

## Segurança e privacidade

O BLOOM SAFE é análise local limitada. O hash confirma correspondência com o hash servido pela API, não legitimidade ou segurança do publicador. O backend aceita jogos e fornece downloads, portanto configure limite de upload, armazenamento/backup, rate limits no proxy, moderação operacional e política de remoção antes de uso público. Trate todos os jogos de terceiros como potencialmente perigosos. Não clique em executar/abra manualmente um jogo a menos que confie na origem e tenha proteção adequada. Esta versão não confina processos e não afirma que um pacote é 100% seguro.


## Recursos adicionados nesta atualização (estado e limites)

- **12 opções de idioma**: português do Brasil, inglês, espanhol, francês, alemão, italiano, japonês, coreano, chinês simplificado, russo, árabe e hindi. A navegação e os controles principais têm tradução inicial; mensagens de erro, termos e parte do conteúdo podem permanecer em português/inglês. Isto ainda não é tradução editorial completa.
- **Comunidade e gestão**: aceite explícito da versão 1.0 dos termos no cadastro; exclusão de posts, comentários e projetos próprios; avatar e capa opcionais. A API também impede que um usuário apague conteúdo de outra pessoa.
- **Chats**: conversa privada entre dois perfis e grupos de pelo menos três pessoas, com histórico e exclusão da própria mensagem. As mensagens são armazenadas pelo servidor, não têm criptografia ponta a ponta; não trate chats como canal secreto.
- **Triagem de segurança**: regras simples por palavras/nomes/metadados sinalizam termos de pirataria, conteúdo adulto e violência; executáveis/scripts no ZIP são enviados para revisão. Se `clamscan` (ClamAV) estiver instalado no servidor, ele é chamado opcionalmente. Sem ele, a resposta informa `antivirus_status: unavailable`. Análise de nomes/textos e ClamAV **não detectam todo malware**, não analisam visualmente imagens/cenas, não provam titularidade autoral e não substituem moderação humana. Pacote sinalizado permanece oculto do catálogo até aprovação de um moderador.
- **Operação de moderação**: configure `BLOOM_MODERATOR_USER_IDS` com IDs numéricos de contas controladas pelo responsável do serviço. Sem moderador configurado, publicações sinalizadas não poderão ser aprovadas pelo cliente. Descubra o ID autenticado em `GET /api/me` e configure essa variável no ambiente privado do servidor; nunca coloque credenciais/moderadores no aplicativo distribuído.
- **BLOOM MAKER 2D**: objetos de cena, blocos por evento (iniciar/clicar), movimento, texto, cor, imagens e áudio; projeto salvável e exportação ZIP. A prévia executa somente os blocos básicos implementados. Os pacotes baixados continuam sem runtime executável dentro do BLOOM; jogos externos são extraídos, não iniciados. 3D, runtime de jogos publicáveis, física/colisão, moderação visual automática, tradução integral, criptografia de chat e revisão/denúncias com equipe são trabalho futuro.
- **Termos**: consulte [TERMS.md](TERMS.md). É um modelo inicial, precisa de revisão jurídica antes de lançamento público/comercial.

Antes de publicar uma versão, rode `python -m pytest -q`, teste os fluxos em duas contas e configure moderadores e política de operação. Uma suíte verde não equivale a auditoria de segurança nem a serviço pronto para escala.
