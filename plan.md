# BLOOM — plano de evolução web

## Escopo e arquitetura

Preservar integralmente o cliente Tkinter, o BLOOM MAKER, o BLOOM SAFE, a API FastAPI, o esquema persistente, os termos, os testes e o histórico Git de `zyxzxm/bloom`. Acrescentar um cliente web responsivo em `web/` e servi-lo pelo próprio `bloom_world` no mesmo host dos endpoints existentes. O navegador usará a API real, JWT Bearer e os limites/autorização já definidos no servidor; nenhuma ação social, mensagem ou publicação será simulada. A aplicação web é o novo companion do desktop, não uma substituição silenciosa das capacidades locais do Windows.

A implementação será estática (HTML, CSS e JavaScript moderno, sem framework de runtime), com chamadas `fetch` ao mesmo origin e configuração de URL de API persistida para instalações separadas. O Dockerfile copiará os arquivos web. O frontend cobrirá conta/termos, feed/comentários/curtidas, busca de pessoas/perfil/bio/avatar, loja/filtros/detalhes/avaliação/download, publicação real de ZIP, denúncias, grupos e conversas com polling de mensagens. Um painel de chat global fica disponível sobre todas as rotas. O mini Maker web salva rascunhos no dispositivo; o Maker Python preserva os recursos e exports existentes. A biblioteca, instalação e execução local continuam no desktop porque a API não oferece esses endpoints.

## Estrutura

- `web/index.html`: entrada semântica, metadados responsivos e shell acessível.
- `web/app.css`: design system Frutiger Aero/Green Aero/Aqua Aero/Technozen, estados, animações, foco, reduced-motion e breakpoints mobile.
- `web/app.js`: navegação SPA, autenticação/API, feed, loja, perfis, publicação, chat, denúncias e mini Maker local; Web Audio para a trilha de ambiente.
- `web/assets/`: ilustrações originais planejadas para hero e ambiente Aqua Aero, áudio aprovado e marcas vetoriais das redes sociais.
- `bloom_world/main.py`: montagem dos recursos web na rota raiz sem alterar endpoints existentes.
- `Dockerfile`: incluir os assets web no container já usado pelo Render.
- `tests/`: preservar e expandir checagens do backend e do contrato de servir a interface.
- `docs/asset-licenses.md`: fontes, licença, proveniência e uso de ativos incorporados.
- `README.md`: instalação/execução web, limitações verdadeiras, mobile, endpoints e testes.
- `TODO.md`: critérios de resultado rastreados a este pedido.

## Design

**Movimento:** Frutiger Aero com Aqua Aero, Green Aero e Technozen contemporâneos.

**Princípios centrais:** interface tátil que lembra vidro e água; ecologia luminosa combinada com tecnologia alegre; organização de comunidade densa sem ficar caótica; cada controle aciona uma função conectada à API real ou é identificado como recurso local.

**Filosofia de cor:** ciano oceânico e azul-céu formam a atmosfera; esmeralda e lima comunicam vida; coral/laranja pontuam energia; branco perolado mantém leitura. Evitar cinza como cor identitária e manter contraste nos controles translúcidos.

**Paradigma de layout:** app-shell assimétrico com trilho de navegação lateral, feed principal em coluna, módulos vivos de descoberta à direita e chat flutuante persistente; no celular, navegação inferior de toque e painéis em tela cheia.

**Elementos assinatura:** orbe de vidro/prisma com reflexos e partículas; ilustrações panorâmicas oceano-jardim; superfícies translúcidas polidas com bordas luminosas.

**Interação:** hover/tap faz controles responderem como superfícies vivas (inclinação leve, brilho, press); feedback de sucesso/erro e loading sempre contextual; modais com Escape/foco e botões com rótulos claros.

**Animação:** bolhas lentas, névoa cromática e luz ambiental no fundo; transições curtas de página/cards; entrada progressiva sem travar leitura. Respeitar `prefers-reduced-motion`, suspender partículas fora de foco e evitar movimento forte no mobile.

**Tipografia:** `Trebuchet MS`/system humanist sans para interface e headlines; pilha system-ui para conteúdo; pesos 600–800 e escala fluida com `clamp`.

**Essência:** o jardim oceânico onde comunidades indie publicam, descobrem e conversam, sem separar natureza e tecnologia. Personalidade: exuberante, acolhedora, explorável.

**Voz:** otimista e concreta, sem filler genérico. Exemplos: “A próxima ideia floresce por aqui.” / “Encontre seu próximo mundo.”

**Wordmark:** BLOOM com letras arredondadas, marca-satélite/esfera de vidro e folha-viva integrada ao O, feita em SVG/CSS e texto exato. **Crédito na interface:** `BLOOM — Created by ZYXZXM.`

**Cor de assinatura:** aqua-lima prismática, com gradiente ciano → verde-lima.

## Pesquisa de estilo e licenças

O Frutiger Aero Archive e o Consumer Aesthetics Research Institute foram usados como referência descritiva e histórica; as imagens de arquivo servem apenas à análise de estilo e não serão copiadas para o projeto. Música de terceiros será incorporada somente após confirmar licença compatível de distribuição pelo repositório/site; suas informações ficarão no documento de licenças, sem ampliar o crédito autoral exibido no produto.
