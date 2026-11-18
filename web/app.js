(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  function safeParse(value) { try { return JSON.parse(value); } catch { return null; } }
  const state = {
    view: 'home', token: localStorage.getItem('bloom.token') || '', user: safeParse(localStorage.getItem('bloom.user')),
    api: (localStorage.getItem('bloom.api') || new URLSearchParams(location.search).get('api') || '').replace(/\/$/, ''), gameQuery: '', category: '', chats: [], activeChat: null,
    messageTimer: null, makerShape: 'circle', makerItems: safeParse(localStorage.getItem('bloom.maker')) || [], soundPlaying: false,
    commentsOpen: new Set(), commentCache: new Map(), searchTimer: null
  };
  const dialog = $('#app-dialog');
  const apiUrl = path => `${state.api}${path}`;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const humanSize = size => size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} KB` : `${(size / 1024 / 1024).toFixed(1)} MB`;
  const when = value => { const d = new Date(value); return Number.isNaN(d.valueOf()) ? 'agora' : d.toLocaleString('pt-BR',{dateStyle:'medium',timeStyle:'short'}); };
  const avatar = (username, small = false) => `<span class="${small ? 'avatar-small' : 'user-avatar'}">${username ? `<img alt="" loading="lazy" src="${apiUrl(`/api/users/${encodeURIComponent(username)}/avatar`)}" onerror="this.remove()">` : '✿'}</span>`;
  const toast = (message, kind = 'success') => { const node = document.createElement('div'); node.className = `toast ${kind}`; node.textContent = message; $('#toast-region').append(node); setTimeout(() => node.remove(), 3600); };
  const explainError = async response => {
    try { const data = await response.json(); const detail = data.detail; return typeof detail === 'string' ? detail : detail?.detail || (Array.isArray(detail?.findings) ? `${detail.detail}: ${detail.findings.join(', ')}` : JSON.stringify(detail)); }
    catch { return `Falha ${response.status}: ${response.statusText || 'resposta inesperada'}`; }
  };
  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (state.token) headers.set('Authorization', `Bearer ${state.token}`);
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type','application/json');
    let response;
    try { response = await fetch(apiUrl(path), {...options, headers}); }
    catch { throw new Error('Não foi possível conectar à API BLOOM. Confira o endereço em Configurações e tente novamente.'); }
    if (!response.ok) throw new Error(await explainError(response));
    if (response.status === 204) return null;
    const type = response.headers.get('content-type') || '';
    return type.includes('application/json') ? response.json() : response;
  }
  const requireUser = () => { if (state.user && state.token) return true; openAuth('login'); return false; };
  const viewTitle = {home:'Seu jardim',feed:'Comunidade',explore:'Explorar mundos',maker:'Maker studio',profile:'Meu perfil'};
  function setView(view, query = '') {
    const allowed = ['home','feed','explore','maker','profile']; state.view = allowed.includes(view) ? view : 'home';
    if (query) state.gameQuery = query;
    history.replaceState(null,'',`#${state.view}`);
    $$('.nav-item[data-view],.mobile-tab[data-view]').forEach(btn => btn.classList.toggle('active', btn.dataset.view === state.view));
    $('#page-title').textContent = viewTitle[state.view] || view;
    $('#global-search').value = state.view === 'explore' ? state.gameQuery : '';
    renderView();
  }
  function notSignedIn(message = 'Entre na sua conta para continuar.'){ return `<section class="empty-card not-signed-in"><div class="empty-art">✿</div><h3>Seu lugar está florescendo</h3><p>${esc(message)}</p><button class="button-primary" data-action="auth">Entrar ou criar conta</button></section>`; }
  function pageTitle(kicker,title,description,action=''){ return `<div class="page-title-row"><div><span class="micro-label">${esc(kicker)}</span><h1>${esc(title)}</h1><p>${esc(description)}</p></div>${action}</div>`; }
  function renderHome(){
    $('#view-root').innerHTML = `<section class="hero"><img class="hero-image" src="/assets/aero-world-2026.webp" alt="Ilha-jardim luminosa sobre um oceano azul, sob bolhas de vidro" fetchpriority="high"><div class="hero-copy"><span class="eyebrow"><i></i> A COMUNIDADE CRIATIVA, EM FLOR</span><h1>A world of<br><em>color, nature</em><br>and technology.</h1><p>Compartilhe ideias, descubra jogos independentes e encontre pessoas que estão criando mundos novos.</p><div class="hero-ctas"><button class="button-primary" data-view="explore">Explorar mundos <span>↗</span></button><button class="button-glass" data-view="feed">Visitar a comunidade</button></div></div><div class="hero-chip">UM JARDIM DE POSSIBILIDADES<strong>Floresça no seu ritmo ✿</strong></div></section>
      <section class="garden-panel"><img src="/assets/aero-garden-2026.webp" alt="Estufa de vidro tropical sobre água cristalina" loading="lazy"><div class="garden-panel-copy"><span class="micro-label">UM REFÚGIO NO MEIO DO OCEANO</span><h2>Respire. Explore.<br>Deixe a ideia brotar.</h2><p>Uma paisagem viva acompanha seu passeio pelo BLOOM.</p><button class="button-glass" data-view="explore">Entrar no jardim <span>↗</span></button></div></section><div class="section-heading"><div><span class="micro-label">ESCOLHA SEU CAMINHO</span><h2>Há vida por aqui.</h2></div><button class="text-cta" data-view="explore">Ver tudo <span>→</span></button></div>
      <div class="fresh-row"><button class="feature-card" data-view="feed"><span class="feature-icon">✿</span><h3>Encontre sua comunidade</h3><p>Conversas, ideias e projetos compartilhados.</p><span class="feature-arrow">↗</span></button><button class="feature-card" data-view="explore"><span class="feature-icon">◎</span><h3>Explore outros mundos</h3><p>Jogos indie publicados pela comunidade.</p><span class="feature-arrow">↗</span></button><button class="feature-card" data-view="maker"><span class="feature-icon">✦</span><h3>Dê forma às ideias</h3><p>Abra o estúdio e crie uma cena para salvar.</p><span class="feature-arrow">↗</span></button></div>
      <div class="content-grid"><section class="feed-column"><div class="section-heading"><div><span class="micro-label">DE QUEM ESTÁ POR PERTO</span><h2>Brota no feed.</h2></div><button class="text-cta" data-view="feed">Abrir comunidade <span>→</span></button></div><div id="home-feed" class="loading-state">Sintonizando o jardim…</div></section><aside class="feed-side-note"><div class="mini-bubbles"><i></i><i></i><i></i></div><span class="micro-label">SOM DO JARDIM</span><h4>Ritmo de maré.</h4><p>Uma trilha calma acompanha os seus passeios. Ative a música quando quiser, no controle do menu.</p><button class="button-quiet" data-action="sound">Abrir controles musicais</button></aside></div>`;
    loadPosts(4,'#home-feed',true); loadGames('', '', true);
  }
  function postCard(post, preview = false){
    const own = Number(state.user?.id) === Number(post.author_id);
    const liked = post.liked === true;
    return `<article class="post-card" data-post-id="${post.id}"><header class="post-head">${avatar(post.author)}<div class="post-meta"><strong>${esc(post.author || 'jardineiro')}</strong><small>${when(post.created_at)}</small></div><button class="report-button" data-action="report" data-kind="post" data-id="${post.id}" aria-label="Denunciar publicação">Denunciar</button>${own ? `<button class="report-button" data-action="delete-post" data-id="${post.id}" aria-label="Apagar publicação">Apagar</button>` : ''}</header><p class="post-body">${esc(post.body)}</p><div class="post-actions"><button class="post-action ${liked?'liked':''}" data-action="like" data-id="${post.id}" ${state.user?'':'title="Entre para curtir"'}>♡ ${post.likes ?? 0} gostei</button><button class="post-action" data-action="comments" data-id="${post.id}">◌ ${post.comments ?? 0} conversa${Number(post.comments)===1?'':'s'}</button>${preview?`<button class="post-action" data-view="feed">Abrir →</button>`:''}</div><div class="comments-box" id="comments-${post.id}" ${state.commentsOpen.has(String(post.id))?'':'hidden'}><div class="comment-list">${state.commentCache.has(String(post.id))?state.commentCache.get(String(post.id)).map(c=>`<div class="comment-row"><strong>${esc(c.author)}</strong> ${esc(c.body)} ${Number(c.author_id)===Number(state.user?.id)?`<button class="report-button" data-action="delete-comment" data-id="${c.id}">Apagar</button>`:''}</div>`).join(''):'<span class="form-helper">Carregando…</span>'}</div>${state.user?`<form class="comment-entry" data-form="comment" data-id="${post.id}"><input name="body" maxlength="2000" placeholder="Deixe uma resposta…" required aria-label="Escreva um comentário"><button class="button-quiet">Enviar</button></form>`:`<button class="button-quiet" data-action="auth">Entre para comentar</button>`}</div></article>`;
  }
  async function loadPosts(limit = 30, selector = '#feed-list', preview = false){
    const host = $(selector); if (!host) return;
    try { const posts = await api(`/api/posts?limit=${limit}&offset=0`); host.innerHTML = posts.length ? posts.map(p=>postCard(p,preview)).join('') : `<section class="empty-card"><div class="empty-art">☼</div><h3>Este pedaço do jardim está quieto.</h3><p>Uma conversa pode começar com uma frase curta, uma descoberta ou uma imagem do que você está criando.</p>${state.user?`<button class="button-soft" data-action="focus-composer">Plantar a primeira ideia</button>`:`<button class="button-soft" data-action="auth">Entrar e começar</button>`}</section>`; }
    catch (error) { host.innerHTML = `<section class="empty-card"><h3>O feed não respondeu.</h3><p>${esc(error.message)}</p><button class="button-quiet" data-action="reload-feed">Tentar novamente</button></section>`; }
  }
  function renderFeed(){
    $('#view-root').innerHTML = `${pageTitle('IDEIAS EM CIRCULAÇÃO','Comunidade','Um canto aberto para projetos, perguntas e pequenos momentos.','<button class="button-soft" data-action="reload-feed">Atualizar ↻</button>')}
      ${state.user?`<form class="post-composer" data-form="post"><div class="composer-row">${avatar(state.user.username)}<textarea class="composer-input" name="body" maxlength="4000" placeholder="O que está florescendo hoje, ${esc(state.user.username)}?" required></textarea></div><div class="composer-bottom"><span class="hint-text">Sem pressa. Compartilhe com gentileza.</span><button class="button-primary">Publicar ✿</button></div></form>`:notSignedIn('Entre ou crie uma conta para publicar e conversar na comunidade.')}
      <div id="feed-list" class="feed-column loading-state">Abrindo o jardim…</div>`;
    loadPosts(50,'#feed-list');
  }
  async function loadGames(q = '', category = '', compact = false){
    const host = compact ? $('#trending-list') : $('#games-list'); if (!host) return;
    try {
      const params = new URLSearchParams(); if(q)params.set('q',q); if(category)params.set('category',category);
      const games = await api(`/api/games?${params}`);
      if (compact) { host.innerHTML = games.length ? games.slice(0,3).map((g,i)=>`<div class="trend-row"><span class="trend-art">${['✧','◌','✦'][i]}</span><div class="trend-meta"><strong>${esc(g.name)}</strong><small>${esc(g.format)} · ${esc(g.developer)}</small></div><span class="trend-rating">${g.rating?`★ ${Number(g.rating).toFixed(1)}`:'NEW'}</span></div>`).join('') : `<div class="form-helper">Ainda não há mundos publicados. Você pode iniciar um jardim novo.</div>`; return; }
      host.classList.remove('loading-state'); host.innerHTML = games.length ? games.map(gameCard).join('') : `<section class="empty-card"><div class="empty-art">◉</div><h3>Nenhum mundo combinou com a busca.</h3><p>Experimente outro nome ou crie um pacote para inaugurar uma nova trilha.</p>${state.user?`<button class="button-soft" data-action="publish-game">Publicar um jogo</button>`:''}</section>`;
    } catch(error){ if(!host) return; host.classList.remove('loading-state'); host.innerHTML=`<section class="empty-card"><h3>O catálogo está fora do alcance agora.</h3><p>${esc(error.message)}</p><button class="button-quiet" data-action="reload-games">Tentar de novo</button></section>`; }
  }
  function gameCard(g){
    const cover = g.cover_url ? `${state.api}${g.cover_url}` : '';
    return `<article class="game-card" data-action="game-detail" data-slug="${esc(g.slug)}"><div class="game-cover">${cover?`<img src="${esc(cover)}" alt="Capa de ${esc(g.name)}" loading="lazy" onerror="this.remove()">`:'<div class="cover-placeholder" aria-hidden="true"></div>'}<span class="game-format">${esc(g.format)}</span></div><div class="game-info"><h3>${esc(g.name)}</h3><p>${esc(g.description || 'Um mundo independente, criado por alguém da comunidade.')}</p><div class="game-byline"><span>por ${esc(g.developer)}</span><span class="rating-stars">${g.rating?`★ ${Number(g.rating).toFixed(1)}`:'☆ novo'}</span></div><div class="game-actions"><button class="button-quiet" data-action="game-detail" data-slug="${esc(g.slug)}">Conhecer</button><span class="form-helper">${humanSize(g.size||0)}</span></div></div></article>`;
  }
  function renderExplore(){
    $('#view-root').innerHTML = `${pageTitle('MAPA DE DESCOBERTAS','Explore outros mundos','Uma vitrine da comunidade. Baixe pacotes sabendo o que está recebendo.','<button class="button-primary" data-action="publish-game">Publicar um jogo ＋</button>')}
    <section class="explore-banner"><img class="explore-banner-image" src="/assets/aero-garden-2026.webp" alt="Estufa-jardim luminosa junto ao oceano" loading="lazy"><div class="explore-banner-copy"><span class="eyebrow"><i></i> CADA PACOTE É UM UNIVERSO</span><h2>Pequenos jogos.<br>Grandes constelações.</h2><p>Explore projetos feitos por criadores independentes e confira os detalhes antes de baixar.</p></div></section>
    <div class="filter-row" role="group" aria-label="Filtrar jogos"><button class="filter-chip ${state.category===''?'active':''}" data-action="filter-game" data-category="">Todos os formatos</button><button class="filter-chip ${state.category==='bloom'?'active':''}" data-action="filter-game" data-category="bloom">BLOOM</button><button class="filter-chip ${state.category==='pygame'?'active':''}" data-action="filter-game" data-category="pygame">Pygame</button><button class="filter-chip ${state.category==='exe'?'active':''}" data-action="filter-game" data-category="exe">Executável</button><button class="filter-chip" data-action="reload-games">Atualizar ↻</button></div>
    <div id="games-list" class="games-grid loading-state">Alinhando as estrelas…</div>`;
    if (state.gameQuery) { $('#global-search').value=state.gameQuery; }
    loadGames(state.gameQuery,state.category);
  }
  function makerShape(x,y,type){return {id:`s${Date.now()}${Math.floor(Math.random()*999)}`,x,y,type,label:type==='circle'?'orbe':'folha'};}
  function saveMaker(){localStorage.setItem('bloom.maker',JSON.stringify(state.makerItems));}
  function makerMarkup(){return state.makerItems.map(s=>`<div class="stage-shape ${s.type==='circle'?'circle':'rect'}" data-shape-id="${esc(s.id)}" style="left:${s.x}%;top:${s.y}%" tabindex="0" aria-label="${esc(s.label)}">${esc(s.label)}</div>`).join('');}
  function renderMaker(){
    $('#view-root').innerHTML=`${pageTitle('ESTÚDIO PESSOAL','Maker Studio','Experimente formas numa cena 2D e salve um rascunho neste dispositivo.','<button class="button-soft" data-action="export-scene">Exportar JSON ↓</button>')}
    <div class="form-alert">Este editor web salva localmente e exporta uma cena JSON simples. O BLOOM MAKER desktop preserva o formato de projeto e ZIP original; esta cena web não é um runtime de jogo.</div>
    <section class="maker-board"><div class="maker-tools"><button class="button-quiet" data-action="add-shape" data-shape="circle">＋ Orbe</button><button class="button-quiet" data-action="add-shape" data-shape="rect">＋ Folha</button><button class="button-quiet" data-action="clear-scene">Limpar cena</button><span class="form-helper">${state.makerItems.length} objeto(s)</span></div><div class="maker-workspace"><aside class="maker-inspector"><span class="micro-label">FERRAMENTAS</span><h3>Arraste suas formas.</h3><button class="tool-chip ${state.makerShape==='circle'?'active':''}" data-action="set-shape" data-shape="circle">◌ Orbe de vidro</button><button class="tool-chip ${state.makerShape==='rect'?'active':''}" data-action="set-shape" data-shape="rect">✿ Folha viva</button><p class="maker-help">Toque ou clique numa forma nova para selecioná-la. Mova-a para compor a cena.</p></aside><div class="maker-stage" id="maker-stage" aria-label="Tela de composição 2D">${makerMarkup()}</div></div><p class="maker-help">Rascunho guardado automaticamente neste navegador. Não é publicado no servidor.</p></section>`;
    $('#maker-stage')?.addEventListener('pointerdown', makerPointerDown);
  }
  let drag = null;
  function makerPointerDown(event){
    const node=event.target.closest('.stage-shape'); const stage=event.currentTarget; if(!node)return;
    $$('.stage-shape',stage).forEach(el=>el.classList.remove('selected'));node.classList.add('selected');
    drag={id:node.dataset.shapeId,stage,rect:stage.getBoundingClientRect(),pointer:event.pointerId};node.setPointerCapture(event.pointerId);
    node.addEventListener('pointermove',makerPointerMove);node.addEventListener('pointerup',makerPointerUp,{once:true});
  }
  function makerPointerMove(event){if(!drag||event.pointerId!==drag.pointer)return;const item=state.makerItems.find(i=>i.id===drag.id);if(!item)return;item.x=Math.max(0,Math.min(87,(event.clientX-drag.rect.left)/drag.rect.width*100-6));item.y=Math.max(0,Math.min(85,(event.clientY-drag.rect.top)/drag.rect.height*100-5));event.currentTarget.style.left=`${item.x}%`;event.currentTarget.style.top=`${item.y}%`;}
  function makerPointerUp(){saveMaker();drag=null;}
  function renderProfile(){
    if(!state.user){$('#view-root').innerHTML=pageTitle('PERFIL DO JARDIM','Conheça quem cria','Pesquise uma pessoa pelo nome para descobrir seu espaço.')+notSignedIn('Entre para editar seu perfil, ou pesquise perfis públicos pelo campo abaixo.')+`<section class="profile-panel"><label class="micro-label" for="user-search">PROCURAR CRIADORES</label><div class="search-users"><input id="user-search" minlength="2" placeholder="Pelo menos duas letras…"><button class="button-quiet" data-action="search-users">Buscar</button></div><div id="user-results" class="user-results"></div></section>`;return;}
    $('#view-root').innerHTML=`${pageTitle('SUA ESTAÇÃO','Meu perfil','Atualize sua bio e encontre pessoas para conversar.')}
      <section class="profile-panel"><div class="profile-cover"></div><div class="profile-row">${avatar(state.user.username)}<div class="profile-copy"><h2>@${esc(state.user.username)}</h2><p>Membro do BLOOM WORLD</p></div><button class="button-quiet" data-action="logout" style="margin-left:auto">Sair</button></div><p class="profile-bio">${esc(state.user.bio||'Seu jardim está esperando a primeira linha da sua história.')}</p><form class="form-stack" data-form="bio"><div class="form-field"><label for="bio-input">Sua bio</label><textarea id="bio-input" name="body" maxlength="500" required>${esc(state.user.bio||'')}</textarea></div><button class="button-soft">Salvar bio</button></form><form class="form-stack" data-form="avatar"><div class="form-field"><label for="avatar-file">Foto de perfil (PNG, JPEG, WEBP ou GIF; máximo 5 MB)</label><input id="avatar-file" type="file" name="file" accept="image/png,image/jpeg,image/webp,image/gif" required></div><button class="button-quiet">Atualizar avatar</button></form></section>
      <section class="profile-panel" style="margin-top:12px"><span class="micro-label">ENCONTRE SUA PRÓXIMA CONVERSA</span><div class="search-users"><input id="user-search" minlength="2" placeholder="Buscar por nome de usuário…"><button class="button-quiet" data-action="search-users">Buscar</button></div><div id="user-results" class="user-results"></div></section>`;
  }
  function renderView(){
    if(state.messageTimer){clearInterval(state.messageTimer);state.messageTimer=null;}
    if(state.view==='home')renderHome(); else if(state.view==='feed')renderFeed(); else if(state.view==='explore')renderExplore(); else if(state.view==='maker')renderMaker(); else if(state.view==='profile')renderProfile();
  }
  async function authTerms(){try{return await api('/api/terms');}catch(e){return {version:'atual',text:`Não foi possível carregar os termos da API. ${e.message}`};}}
  async function openAuth(mode='login'){
    const terms=mode==='register'?await authTerms():null;
    const register=mode==='register';
    showDialog(register?'Criar conta no jardim':'Entre no BLOOM',register?'Uma conta mantém seus projetos de comunidade entre sessões.':'Retome suas conversas e projetos.',`<form class="form-stack" data-form="auth" data-mode="${register?'register':'login'}"><div class="form-field"><label for="auth-user">Nome de usuário</label><input id="auth-user" name="username" autocomplete="username" minlength="3" maxlength="32" pattern="[A-Za-z0-9_]+" required></div>${register?`<div class="form-field"><label for="auth-email">E-mail</label><input id="auth-email" name="email" type="email" autocomplete="email" maxlength="254" required></div>`:''}<div class="form-field"><label for="auth-pass">Senha</label><input id="auth-pass" name="password" type="password" autocomplete="${register?'new-password':'current-password'}" minlength="${register?'10':'1'}" maxlength="128" required>${register?'<span class="form-helper">Use no mínimo 10 caracteres.</span>':''}</div>${register?`<div class="terms-copy">${esc(terms?.text||'Termos da comunidade')}</div><label class="checkbox-row"><input name="accept_terms" type="checkbox" required><span>Li e aceito os termos ${esc(terms?.version||'vigentes')} e as regras de convivência.</span></label>`:''}<div class="form-error" data-error hidden></div><button class="button-primary">${register?'Florescer ✿':'Entrar no meu jardim'}</button></form><p class="auth-switch">${register?'Já tem conta?':'É sua primeira vez?'} <button type="button" data-action="auth-switch" data-mode="${register?'login':'register'}">${register?'Entrar':'Criar uma conta'}</button></p>`);
  }
  function showDialog(title,subtitle,body){
    dialog.innerHTML=`<div class="dialog-inner"><header class="dialog-head"><div><span class="micro-label">BLOOM WORLD</span><h2>${esc(title)}</h2><p>${esc(subtitle||'')}</p></div><button class="dialog-close" data-action="close-dialog" aria-label="Fechar">×</button></header><div class="dialog-content">${body}</div></div>`;
    if(!dialog.open)dialog.showModal();
    dialog.querySelector('input,textarea,button')?.focus({preventScroll:true});
  }
  function openSettings(){
    showDialog('Configurações','Ajuste a conexão e a trilha que acompanha o passeio.',`<form class="form-stack" data-form="settings"><div class="form-field"><label for="api-field">Endereço da API BLOOM WORLD</label><input id="api-field" name="api" type="url" placeholder="https://bloom-world.onrender.com" value="${esc(state.api||location.origin)}"><span class="form-helper">Deixe vazio para conectar à API no mesmo domínio. Não use credenciais nesta URL.</span></div><button class="button-soft">Salvar endereço</button><button class="button-quiet" type="button" data-action="test-api">Testar conexão</button></form><div class="form-alert" style="margin-top:10px">Conta, publicações e conversas usam a API real. Dados do Maker web e configurações de conexão são locais neste navegador.</div><div class="form-helper" style="margin-top:9px">BLOOM — Created by ZYXZXM.</div>`);
  }
  async function checkHealth(){const badge=$('#api-status')?.parentElement;try{const h=await api('/health');$('#api-status').textContent=h.status==='ok'?'mundo conectado':'resposta da API';badge?.removeAttribute('data-state');}catch{$('#api-status').textContent='API indisponível';badge?.setAttribute('data-state','error');}}
  async function loadComments(postId){
    try{const comments=await api(`/api/posts/${postId}/comments`);state.commentCache.set(String(postId),comments);const box=$(`#comments-${postId}`);if(box){$('.comment-list',box).innerHTML=comments.length?comments.map(c=>`<div class="comment-row"><strong>${esc(c.author)}</strong> ${esc(c.body)} ${Number(c.author_id)===Number(state.user?.id)?`<button class="report-button" data-action="delete-comment" data-id="${c.id}">Apagar</button>`:''}</div>`).join(''):'<span class="form-helper">Ainda não há respostas. Você pode abrir a conversa.</span>';}}catch(e){toast(e.message,'error');}
  }
  async function openGame(slug){
    try{const g=await api(`/api/games/${encodeURIComponent(slug)}`);showDialog(g.name,`${g.format} · versão ${g.version} · criado por ${g.developer}`,`<div class="game-cover" style="height:170px;border-radius:15px;margin-top:12px">${g.cover_url?`<img src="${state.api}${esc(g.cover_url)}" alt="Capa de ${esc(g.name)}">`:'<div class="cover-placeholder"></div>'}</div><p class="post-body">${esc(g.description)}</p><div class="storage-note">Pacote ${humanSize(g.size)} · SHA-256 <code>${esc(g.sha256)}</code><br>A triagem automática é limitada. Baixar não executa o arquivo. Confira o conteúdo com cuidado antes de abrir.</div><div class="form-stack"><label class="form-field"><span>Avalie este projeto</span><select id="game-rating"><option value="">Escolha de 1 a 5 estrelas</option>${[1,2,3,4,5].map(n=>`<option value="${n}">${'★'.repeat(n)} · ${n}</option>`).join('')}</select></label><div class="maker-tools"><button class="button-soft" data-action="rate-game" data-id="${g.id}">Enviar avaliação</button><button class="button-primary" data-action="download-game" data-slug="${esc(g.slug)}" data-hash="${esc(g.sha256)}">Baixar ZIP ↓</button><button class="button-quiet" data-action="report" data-kind="game" data-id="${g.id}">Denunciar</button>${Number(state.user?.id)===Number(g.developer_id)?`<button class="button-quiet" data-action="delete-game" data-id="${g.id}">Remover</button>`:''}</div></div>`);}
    catch(e){toast(e.message,'error');}
  }
  async function downloadGame(button){
    try{button.disabled=true;button.textContent='Conferindo pacote…';const response=await fetch(apiUrl(`/api/games/${encodeURIComponent(button.dataset.slug)}/download`));if(!response.ok)throw new Error(await explainError(response));const blob=await response.blob();const expected=(response.headers.get('X-Content-SHA256')||button.dataset.hash||'').toLowerCase();if(expected&&crypto.subtle){const digest=await crypto.subtle.digest('SHA-256',await blob.arrayBuffer());const actual=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');if(actual!==expected)throw new Error('A verificação SHA-256 não correspondeu. O ZIP não foi salvo.');}const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=`${button.dataset.slug}.zip`;link.click();URL.revokeObjectURL(link.href);toast('Pacote conferido e baixado. O BLOOM não abre o jogo automaticamente.');}
    catch(e){toast(e.message,'error');}finally{button.disabled=false;button.textContent='Baixar ZIP ↓';}
  }
  function openPublish(){
    if(!requireUser())return;
    showDialog('Publicar um mundo','Um arquivo ZIP válido, com manifesto bloom.json na raiz.',`<form class="form-stack" data-form="publish"><div class="form-alert">Formatos aceitos: bloom, pygame ou exe. Cada pacote precisa de <code>bloom.json</code> com nome, versão, desenvolvedor, descrição, formato, lista de arquivos e ponto de entrada. O conteúdo não é executado. O tamanho máximo na nuvem configurada é 45 MB (local: 300 MB).</div><div class="form-field"><label>Nome do jogo</label><input name="name" minlength="1" maxlength="100" required></div><div class="form-field"><label>Versão</label><input name="version" maxlength="40" placeholder="1.0.0" required></div><div class="form-field"><label>Descrição</label><textarea name="description" maxlength="10000" required></textarea></div><div class="form-field"><label>Formato</label><select name="format"><option value="bloom">BLOOM</option><option value="pygame">Pygame</option><option value="exe">Executável</option></select></div><label class="file-drop">Pacote de jogo (.zip)<input name="file" type="file" accept=".zip,application/zip" required></label><label class="file-drop">Imagem de capa opcional<input name="cover" type="file" accept="image/png,image/jpeg,image/webp,image/gif"></label><div class="form-error" data-error hidden></div><button class="button-primary">Enviar para revisão ✿</button></form>`);
  }
  function openReport(kind,id){if(!requireUser())return;showDialog('Sinalizar conteúdo','A equipe responsável avaliará esta denúncia.',`<form class="form-stack" data-form="report" data-kind="${esc(kind)}" data-id="${esc(id)}"><div class="form-field"><label>Conte brevemente o motivo</label><textarea name="reason" minlength="5" maxlength="1000" required placeholder="O que precisa de atenção?"></textarea></div><div class="form-error" data-error hidden></div><button class="button-soft">Enviar denúncia</button></form>`);}
  function updateAccount(){
    const signed=Boolean(state.token&&state.user);$('#account-name').textContent=signed?`@${state.user.username}`:'Entrar';$('#account-avatar').innerHTML=signed?`${esc(state.user.username.slice(0,1).toUpperCase())}`:'✿';
    if(signed){const img=new Image();img.src=apiUrl(`/api/users/${encodeURIComponent(state.user.username)}/avatar`);img.onload=()=>{$('#account-avatar').innerHTML=`<img alt="" src="${img.src}">`;};img.onerror=()=>{};}
    $('#chat-fab').setAttribute('aria-label',signed?'Abrir conversas':'Entrar para conversar');
  }
  async function openChat(){
    if(!requireUser())return;
    const dock=$('#chat-dock');dock.hidden=false;
    await loadChats();
    if(state.activeChat)await loadMessages(state.activeChat);
  }
  async function loadChats(){
    try{state.chats=await api('/api/chats');renderChatDock();if(state.activeChat&&!state.chats.some(c=>Number(c.id)===Number(state.activeChat)))state.activeChat=null;if(!state.activeChat&&state.chats[0])state.activeChat=state.chats[0].id;renderChatDock();if(state.activeChat)await loadMessages(state.activeChat);}
    catch(e){if(!$('#chat-dock').hidden)toast(e.message,'error');}
  }
  function renderChatDock(){
    const dock=$('#chat-dock');if(dock.hidden)return;
    const current=state.chats.find(c=>Number(c.id)===Number(state.activeChat));
    dock.innerHTML=`<header class="chat-dock-head"><div><h3>Conversas em flor</h3><small>${state.chats.length} conversa(s) · mensagens são persistidas</small></div><button class="dialog-close" data-action="close-chat" aria-label="Fechar conversas">×</button></header><div class="chat-dock-body"><div class="chat-list">${state.chats.map(c=>`<button class="chat-list-item ${Number(c.id)===Number(state.activeChat)?'active':''}" data-action="select-chat" data-id="${c.id}"><strong>${esc(c.is_group?c.title:(c.members||[]).filter(n=>n!==state.user.username).join(', ')||c.title||'Conversa')}</strong><small>${esc(c.last_message||'Abra a conversa')}</small></button>`).join('')||'<div class="thread-empty">Nenhuma conversa ainda.<br>Comece com uma mensagem direta.</div>'}</div><div class="chat-thread"><div class="thread-head">${current?esc(current.is_group?current.title:(current.members||[]).filter(n=>n!==state.user.username).join(', ')||current.title):'Escolha ou inicie uma conversa'}</div><div id="thread-messages" class="thread-messages">${current?'<div class="thread-empty">Carregando mensagens…</div>':'<div class="thread-empty">Suas conversas abrem aqui.<br>Mensagens do BLOOM não têm criptografia ponta a ponta.</div>'}</div>${current?`<form class="thread-compose" data-form="message" data-id="${current.id}"><input name="body" maxlength="4000" autocomplete="off" placeholder="Escreva com gentileza…" required aria-label="Nova mensagem"><button class="button-quiet">Enviar</button></form>`:''}</div></div><footer class="chat-dock-foot"><button class="button-quiet" data-action="new-direct">＋ Direta</button><button class="button-quiet" data-action="new-group">＋ Grupo</button><button class="button-quiet" data-action="refresh-chats">↻</button></footer>`;
    if(state.messageTimer)clearInterval(state.messageTimer);if(state.activeChat)state.messageTimer=setInterval(()=>loadMessages(state.activeChat,true),7500);
  }
  async function loadMessages(id,silent=false){
    if(!id)return;
    try{const messages=await api(`/api/chats/${id}/messages?limit=100`);if(Number(id)!==Number(state.activeChat))return;const node=$('#thread-messages');if(!node)return;node.innerHTML=messages.length?messages.map(m=>`<div class="chat-bubble ${Number(m.sender_id)===Number(state.user.id)?'mine':''}">${esc(m.body)}<small>${esc(m.sender)} · ${when(m.created_at)} ${Number(m.sender_id)===Number(state.user.id)?`<button class="report-button" data-action="delete-message" data-chat="${id}" data-id="${m.id}">Apagar</button>`:`<button class="report-button" data-action="report" data-kind="message" data-id="${m.id}">Denunciar</button>`}</small></div>`).join(''):'<div class="thread-empty">Esta conversa está pronta para começar.</div>';node.scrollTop=node.scrollHeight;}
    catch(e){if(!silent)toast(e.message,'error');}
  }
  async function openDirect(){
    if(!requireUser())return;
    showDialog('Começar conversa','Mensagens diretas são guardadas pela API e visíveis aos participantes.',`<form class="form-stack" data-form="direct"><div class="form-field"><label>Nome de usuário</label><input name="username" minlength="3" maxlength="32" required></div><div class="form-error" data-error hidden></div><button class="button-soft">Abrir conversa</button></form>`);
  }
  function openGroup(){
    if(!requireUser())return;
    showDialog('Criar grupo','Adicione pelo menos mais duas pessoas além de você.',`<form class="form-stack" data-form="group"><div class="form-field"><label>Nome do grupo</label><input name="title" minlength="2" maxlength="100" required></div><div class="form-field"><label>Participantes — nomes separados por vírgula (mínimo 2)</label><input name="usernames" placeholder="amiga, criador" required></div><div class="form-error" data-error hidden></div><button class="button-soft">Criar grupo</button></form>`);
  }
  function openUserSearch(){
    const field=$('#user-search');const q=field?.value.trim();if(!q||q.length<2){toast('Digite pelo menos duas letras para buscar pessoas.','error');return;}
    searchUsers(q);
  }
  async function searchUsers(q){
    const result=$('#user-results');if(!result)return;result.innerHTML='<div class="loading-state">Procurando pessoas…</div>';
    try{const users=await api(`/api/users/search?q=${encodeURIComponent(q)}`);result.innerHTML=users.length?users.map(u=>`<article class="user-result">${avatar(u.username)}<strong>@${esc(u.username)}</strong><button class="button-quiet" data-action="user-profile" data-user="${esc(u.username)}">Perfil</button><button class="button-quiet" data-action="dm-user" data-user="${esc(u.username)}">Mensagem</button></article>`).join(''):'<div class="form-helper">Ainda não encontramos esse nome.</div>';}
    catch(e){result.innerHTML=`<span class="form-helper">${esc(e.message)}</span>`;}
  }
  async function showPublicUser(username){
    try{const u=await api(`/api/users/${encodeURIComponent(username)}`);showDialog(`@${u.username}`,'Perfil público BLOOM',`<div class="profile-row">${avatar(u.username)}<div class="profile-copy"><h2>${esc(u.username)}</h2><p>Membro desde ${new Date(u.created_at).toLocaleDateString('pt-BR')}</p></div></div><p class="profile-bio">${esc(u.bio||'Este jardim ainda não tem uma bio.')}</p><div class="maker-tools"><button class="button-primary" data-action="dm-user" data-user="${esc(u.username)}">Começar conversa</button><button class="button-quiet" data-action="report" data-kind="user" data-id="${u.id}">Denunciar</button></div>`);}
    catch(e){toast(e.message,'error');}
  }
  async function submitForm(form){
    const kind=form.dataset.form;const fd=new FormData(form);const data=Object.fromEntries(fd.entries());const errorBox=form.querySelector('[data-error]');const button=form.querySelector('button[type="submit"],button:not([type])');
    const fail=e=>{if(errorBox){errorBox.hidden=false;errorBox.textContent=e.message;}else toast(e.message,'error');};
    if(errorBox){errorBox.hidden=true;errorBox.textContent='';}if(button){button.disabled=true;button.dataset.original=button.textContent;button.textContent='Enviando…';}
    try{
      if(kind==='auth'){
        const register=form.dataset.mode==='register';if(register&&!form.elements.accept_terms.checked)throw new Error('Aceite os termos para criar sua conta.');
        const result=await api(register?'/api/auth/register':'/api/auth/login',{method:'POST',body:JSON.stringify(register?{username:data.username,email:data.email,password:data.password,accept_terms:true}:{username:data.username,password:data.password})});
        state.token=result.access_token;state.user=result.user;localStorage.setItem('bloom.token',state.token);localStorage.setItem('bloom.user',JSON.stringify(state.user));dialog.close();updateAccount();toast(register?'Sua conta floresceu. Bem-vinda(o)!':'Que bom ter você de volta.');renderView();checkHealth();
      }else if(kind==='post'){
        if(!requireUser())return;await api('/api/posts',{method:'POST',body:JSON.stringify({body:data.body.trim()})});form.reset();toast('A ideia floresceu no feed.');loadPosts(50,'#feed-list');
      }else if(kind==='comment'){
        await api(`/api/posts/${form.dataset.id}/comments`,{method:'POST',body:JSON.stringify({body:data.body.trim()})});form.reset();state.commentsOpen.add(String(form.dataset.id));await loadComments(form.dataset.id);toast('Resposta publicada.');
      }else if(kind==='bio'){
        const u=await api('/api/me/bio',{method:'PUT',body:JSON.stringify({body:data.body})});state.user=u;localStorage.setItem('bloom.user',JSON.stringify(u));toast('Bio atualizada.');renderProfile();updateAccount();
      }else if(kind==='avatar'){
        const file=fd.get('file');if(!file?.size)throw new Error('Escolha uma imagem para continuar.');const upload=new FormData();upload.append('file',file);await api('/api/me/avatar',{method:'PUT',body:upload});toast('Avatar atualizado.');renderProfile();updateAccount();
      }else if(kind==='settings'){
        state.api=data.api.trim().replace(/\/$/,'');localStorage.setItem('bloom.api',state.api);dialog.close();checkHealth();toast('Endereço de API salvo neste navegador.');
      }else if(kind==='report'){
        await api('/api/reports',{method:'POST',body:JSON.stringify({target_type:form.dataset.kind,target_id:Number(form.dataset.id),reason:data.reason.trim()})});dialog.close();toast('Denúncia enviada à fila de moderação.');
      }else if(kind==='message'){
        await api(`/api/chats/${form.dataset.id}/messages`,{method:'POST',body:JSON.stringify({body:data.body.trim()})});form.reset();await loadMessages(form.dataset.id,true);loadChats();
      }else if(kind==='direct'){
        const chat=await api('/api/chats/direct',{method:'POST',body:JSON.stringify({username:data.username.trim()})});dialog.close();state.activeChat=chat.id;$('#chat-dock').hidden=false;await loadChats();
      }else if(kind==='group'){
        const names=data.usernames.split(',').map(n=>n.trim()).filter(Boolean);if(names.length<2)throw new Error('O grupo precisa de pelo menos mais duas pessoas.');const result=await api('/api/chats/groups',{method:'POST',body:JSON.stringify({title:data.title.trim(),usernames:names})});dialog.close();state.activeChat=result.id;$('#chat-dock').hidden=false;await loadChats();toast('Grupo criado.');
      }else if(kind==='publish'){
        const zip=fd.get('file');if(!zip?.size||!zip.name.toLowerCase().endsWith('.zip'))throw new Error('Selecione um arquivo .zip válido.');const upload=new FormData();['name','version','description','format'].forEach(k=>upload.append(k,data[k]));upload.append('file',zip);const result=await api('/api/games',{method:'POST',body:upload});if(fd.get('cover')?.size){const cover=new FormData();cover.append('file',fd.get('cover'));try{await api(`/api/games/${result.id}/cover`,{method:'PUT',body:cover});}catch(e){toast(`Pacote enviado; a capa não pôde ser salva: ${e.message}`,'error');}}dialog.close();toast(result.status==='published'?'Pacote publicado no catálogo.':`Pacote enviado: ${result.status}.`);setView('explore');
      }
    }catch(e){fail(e);}
    finally{if(button?.isConnected){button.disabled=false;button.textContent=button.dataset.original||'Enviar';}}
  }
  async function handleAction(button){
    const action=button.dataset.action;const id=button.dataset.id;
    if(button.dataset.view){setView(button.dataset.view);return;}
    switch(action){
      case 'auth':openAuth('login');break;
      case 'auth-switch':openAuth(button.dataset.mode);break;
      case 'settings':openSettings();break;
      case 'test-api':try{const h=await api('/health');toast(`Conectado: ${h.service} · ${h.status}`);}catch(e){toast(e.message,'error');}break;
      case 'close-dialog':dialog.close();break;
      case 'open-chat':await openChat();break;
      case 'close-chat':$('#chat-dock').hidden=true;if(state.messageTimer)clearInterval(state.messageTimer);break;
      case 'new-direct':openDirect();break;
      case 'new-group':openGroup();break;
      case 'refresh-chats':await loadChats();break;
      case 'select-chat':state.activeChat=Number(id);renderChatDock();await loadMessages(id);break;
      case 'like':if(requireUser())try{const res=await api(`/api/posts/${id}/like`,{method:'POST'});button.classList.toggle('liked',res.liked);button.innerHTML=`♡ ${res.likes} gostei`; }catch(e){toast(e.message,'error');}break;
      case 'comments':{const key=String(id);const box=$(`#comments-${id}`);if(state.commentsOpen.has(key)){state.commentsOpen.delete(key);box.hidden=true;}else{state.commentsOpen.add(key);box.hidden=false;await loadComments(id);}break;}
      case 'delete-post':if(requireUser()&&confirm('Apagar esta publicação e as respostas associadas?'))try{await api(`/api/posts/${id}`,{method:'DELETE'});toast('Publicação apagada.');loadPosts(state.view==='home'?4:50,state.view==='home'?'#home-feed':'#feed-list',state.view==='home');}catch(e){toast(e.message,'error');}break;
      case 'delete-comment':if(requireUser()&&confirm('Apagar este comentário?'))try{await api(`/api/comments/${id}`,{method:'DELETE'});await loadComments($('[data-action="comments"]')?.dataset.id);toast('Comentário apagado.');}catch(e){toast(e.message,'error');}break;
      case 'report':openReport(button.dataset.kind,id);break;
      case 'filter-game':state.category=button.dataset.category;$$('.filter-chip').forEach(b=>b.classList.toggle('active',b.dataset.category===state.category));loadGames(state.gameQuery,state.category);break;
      case 'reload-games':loadGames(state.gameQuery,state.category);break;
      case 'reload-feed':loadPosts(50,'#feed-list');break;
      case 'game-detail':await openGame(button.dataset.slug);break;
      case 'publish-game':openPublish();break;
      case 'download-game':await downloadGame(button);break;
      case 'rate-game':if(requireUser()){const score=Number($('#game-rating')?.value);if(!score){toast('Escolha uma nota de 1 a 5 estrelas.','error');break;}try{const rating=await api(`/api/games/${id}/rating`,{method:'POST',body:JSON.stringify({score})});toast(`Avaliação recebida. Média da comunidade: ${Number(rating.rating||rating.average||score).toFixed(1)}.`);}catch(e){toast(e.message,'error');}}break;
      case 'delete-game':if(requireUser()&&confirm('Remover o jogo publicado e seu pacote?'))try{await api(`/api/games/${id}`,{method:'DELETE'});dialog.close();toast('Jogo removido.');loadGames(state.gameQuery,state.category);}catch(e){toast(e.message,'error');}break;
      case 'add-shape':{const node=$('#maker-stage');if(!node)break;state.makerItems.push(makerShape(35+Math.random()*30,28+Math.random()*32,button.dataset.shape));saveMaker();renderMaker();break;}
      case 'set-shape':state.makerShape=button.dataset.shape;renderMaker();break;
      case 'clear-scene':if(confirm('Limpar os objetos desta cena?')){state.makerItems=[];saveMaker();renderMaker();}break;
      case 'export-scene':{const file={name:'BLOOM scene',version:1,created_at:new Date().toISOString(),objects:state.makerItems};const blob=new Blob([JSON.stringify(file,null,2)],{type:'application/json'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='bloom-scene.json';link.click();URL.revokeObjectURL(link.href);toast('Cena JSON exportada.');break;}
      case 'focus-composer':$('.composer-input')?.focus();break;
      case 'logout':state.token='';state.user=null;localStorage.removeItem('bloom.token');localStorage.removeItem('bloom.user');dialog.close();updateAccount();toast('Você saiu da conta.');setView('profile');break;
      case 'search-users':openUserSearch();break;
      case 'user-profile':await showPublicUser(button.dataset.user);break;
      case 'dm-user':if(requireUser()){try{const c=await api('/api/chats/direct',{method:'POST',body:JSON.stringify({username:button.dataset.user})});dialog.close();state.activeChat=c.id;$('#chat-dock').hidden=false;await loadChats();}catch(e){toast(e.message,'error');}}break;
      case 'delete-message':if(requireUser()&&confirm('Apagar esta mensagem?'))try{await api(`/api/chats/${button.dataset.chat}/messages/${id}`,{method:'DELETE'});await loadMessages(button.dataset.chat);loadChats();}catch(e){toast(e.message,'error');}break;
      case 'sound':openAudioControls();break;
      case 'toggle-music':await toggleMusic();break;
      default:break;
    }
  }
  function openAudioControls(){
    showDialog('Paisagem sonora','Uma faixa CC0 com filtros Aqua, Green Aero e Technozen.',`<div class="form-stack"><div class="form-field"><label for="portable-mode">Atmosfera</label><select id="portable-mode"><option value="aqua">Aqua Garden · CC0</option><option value="green">Green Aero · filtro vivo</option><option value="zen">Technozen · filtro suave</option></select></div><div class="form-field"><label for="portable-volume">Volume</label><input id="portable-volume" type="range" min="0" max="100" value="${Math.round($('#volume-slider').value)}"></div><button class="button-primary" data-action="toggle-music">${state.soundPlaying?'Pausar música Ⅱ':'Tocar música ▶'}</button><p class="form-helper">A faixa só começa depois do seu toque. O volume também acompanha o controle de música do computador.</p></div>`);
    $('#portable-mode').value=$('#sound-mode').value;
    $('#portable-mode').addEventListener('change',event=>{$('#sound-mode').value=event.target.value;$('#sound-mode').dispatchEvent(new Event('change',{bubbles:true}));});
    $('#portable-volume').addEventListener('input',event=>{$('#volume-slider').value=event.target.value;$('#volume-slider').dispatchEvent(new Event('input',{bubbles:true}));});
  }
  async function toggleMusic(){
    const audio=$('#aqua-track');
    try{
      if(state.soundPlaying){audio.pause();state.soundPlaying=false;$('#sound-glyph').textContent='▶';$('#sound-toggle').setAttribute('aria-label','Tocar música');}
      else{await ensureAudioGraph();await audio.play();state.soundPlaying=true;$('#sound-glyph').textContent='Ⅱ';$('#sound-toggle').setAttribute('aria-label','Pausar música');}
      const modalControl=$('#portable-mode')?.closest('.form-stack')?.querySelector('[data-action="toggle-music"]');if(modalControl)modalControl.textContent=state.soundPlaying?'Pausar música Ⅱ':'Tocar música ▶';
    }catch(e){toast('O navegador bloqueou o áudio. Toque novamente para permitir a trilha.','error');}
  }
  function ensureMobileAudioButton(){
    if($('.mobile-audio-button'))return;
    const button=document.createElement('button');button.type='button';button.className='mobile-audio-button';button.dataset.action='sound';button.setAttribute('aria-label','Controles de música');button.title='Música';button.textContent='♫';
    $('.topbar-actions')?.insertBefore(button,$('#account-button'));
  }
  function bindDesktopTools(){const button=$('#desktop-tools');if(!button)return;const ready=()=>{if(window.pywebview?.api?.open_local_tools){button.hidden=false;button.addEventListener('click',()=>window.pywebview.api.open_local_tools(),{once:false});}};if(window.pywebview?.api)ready();else window.addEventListener('pywebviewready',ready,{once:true});}
  async function verifyDownloadLinks(){for(const a of $$('a[target="_blank"]')){if(!a.rel.includes('noopener'))a.rel='noopener noreferrer';}}
  async function connect(){
    ensureMobileAudioButton();bindDesktopTools();updateAccount();const hash=location.hash.slice(1);if(['home','feed','explore','maker','profile'].includes(hash))state.view=hash;
    setView(state.view);checkHealth();verifyDownloadLinks();
    try{if(state.token){const me=await api('/api/me');state.user=me;localStorage.setItem('bloom.user',JSON.stringify(me));updateAccount();}else updateAccount();}catch{state.token='';state.user=null;localStorage.removeItem('bloom.token');localStorage.removeItem('bloom.user');updateAccount();}
  }
  document.addEventListener('click',event=>{
    const button=event.target.closest('button,[data-action="game-detail"],.brand-lockup');if(!button)return;
    if(button.dataset.view){event.preventDefault();setView(button.dataset.view);return;}
    if(button.dataset.action){event.preventDefault();handleAction(button);}
  });
  document.addEventListener('submit',event=>{const form=event.target.closest('form[data-form]');if(!form)return;event.preventDefault();submitForm(form);});
  $('#global-search').addEventListener('keydown',event=>{if(event.key==='Enter'){state.gameQuery=event.currentTarget.value.trim();state.category='';setView('explore',state.gameQuery);}});
  $('#sound-mode').addEventListener('change',event=>{const labels={aqua:'Aqua Garden',green:'Green Aero',zen:'Technozen'};$('#track-label').textContent=labels[event.target.value]||'Aqua Garden';applySoundMode(event.target.value);});
  $('#volume-slider').addEventListener('input',event=>{const value=Number(event.target.value)/100;const audio=$('#aqua-track');audio.volume=value;if(window.bloomAudioGain)window.bloomAudioGain.gain.value=value;});
  $('#sound-toggle').addEventListener('click',toggleMusic);
  function applySoundMode(mode){const filter=window.bloomAudioFilter;const audio=$('#aqua-track');if(mode==='aqua'){if(filter){filter.type='lowpass';filter.frequency.value=8500;filter.Q.value=.5;}audio.playbackRate=1;}else if(mode==='green'){if(filter){filter.type='lowpass';filter.frequency.value=6100;filter.Q.value=.7;}audio.playbackRate=.97;}else{if(filter){filter.type='lowpass';filter.frequency.value=4200;filter.Q.value=.45;}audio.playbackRate=.92;}}
  async function ensureAudioGraph(){
    if(window.bloomAudioContext){await window.bloomAudioContext.resume();return;}
    const AudioContext=window.AudioContext||window.webkitAudioContext;if(!AudioContext)return;
    const context=new AudioContext();const source=context.createMediaElementSource($('#aqua-track'));const filter=context.createBiquadFilter();const gain=context.createGain();filter.type='lowpass';gain.gain.value=Number($('#volume-slider').value)/100;source.connect(filter);filter.connect(gain);gain.connect(context.destination);window.bloomAudioContext=context;window.bloomAudioFilter=filter;window.bloomAudioGain=gain;applySoundMode($('#sound-mode').value);
  }
  document.addEventListener('input',event=>{if(!event.target.matches('#user-search'))return;clearTimeout(state.searchTimer);const q=event.target.value.trim();if(q.length>=2)state.searchTimer=setTimeout(()=>searchUsers(q),350);});
  dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&dialog.open)dialog.close();});
  window.addEventListener('hashchange',()=>{const next=location.hash.slice(1);if(['home','feed','explore','maker','profile'].includes(next))setView(next);});
  connect();
})();
