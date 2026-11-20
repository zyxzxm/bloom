# BLOOM SAFE, moderação e riscos conhecidos

A publicação chama três verificações limitadas: validação do ZIP e prevenção de ZIP Slip; regras heurísticas em nomes, manifesto e alguns arquivos de texto; e `clamscan` opcional no arquivo enviado quando o binário está instalado no servidor. A resposta da API inclui `antivirus_status` (`clean_by_clamav`, `threat_detected`, `error` ou `unavailable`). Um resultado ClamAV limpo não prova que o jogo é seguro.

Conteúdo sinalizado fica em `pending_review` e não aparece no catálogo até um moderador aprová-lo. Contas de moderador são configuradas no servidor pela variável privada `BLOOM_MODERATOR_USER_IDS`, com IDs numéricos separados por vírgula. `GET /api/me` autenticado informa o ID da própria conta. Moderadores podem consultar `GET /api/moderation/queue`, aprovar/rejeitar projetos com `POST /api/moderation/games/{game_id}` e consultar denúncias com `GET /api/moderation/reports`; resolver/descartar com `POST /api/moderation/reports/{report_id}`. Não configure um moderador público nem inclua essa variável no EXE.

As regras de texto não interpretam contexto nem verificam direitos autorais. Podem gerar falsos positivos e falsos negativos. A API não faz classificação visual de pornografia/gore, não identifica toda pirataria nem detecta todo malware. A implantação Compose padrão não instala ClamAV; nesse caso, `antivirus_status` será `unavailable`. Para antivírus, instale e mantenha ClamAV no ambiente do serviço e monitore atualizações/erros, ou use serviço profissional de análise de arquivos com política de privacidade adequada. Não considere nenhum pacote de terceiros “seguro” apenas porque passou na triagem. A instalação local extrai e verifica hash/caminhos, mas não isola processos; não execute binários desconhecidos.

Chats são armazenados no servidor sem criptografia ponta a ponta. Os participantes e administradores da infraestrutura podem ter acesso técnico às mensagens. Proteja acesso ao banco, cópias, logs, backups e credenciais.


## Proprietário e acesso administrativo

O papel administrativo é resolvido pelo backend a partir de IDs numéricos imutáveis da tabela `users`; editar o nome, bio ou dados de perfil nunca concede privilégios. `BLOOM_OWNER_USER_ID` é uma variável privada de servidor e deve receber o `id` da conta do criador, verificado em sessão autenticada (`GET /api/me`), depois do login legítimo. Não use `@ZYXZXM` como critério de autorização nem exponha esse ID/segredo no cliente. `BLOOM_MODERATOR_USER_IDS` continua aceitando moderadores adicionais definidos pelo operador.

O backend reserva `@ZYXZXM` sem diferenciar maiúsculas/minúsculas para novos cadastros e mudanças de nome; não há mecanismo de autocadastro de proprietário. Até `BLOOM_OWNER_USER_ID` ser configurado no cofre do provedor, nenhuma conta é promovida automaticamente como proprietária. Depois de alterar a variável, reinicie/reimplante a API e confira `/api/me` autenticado. Nunca atribua o ID apenas por um nome público ou conta que não tenha sido verificada pelo próprio titular.

Usuários novos têm username persistido em forma canônica minúscula, verificação de duplicidade no servidor e constraint única de banco; um `IntegrityError` de cadastros simultâneos retorna HTTP 409. Suspensões/banimentos são aplicados a cada autenticação e a cada uso de um token já emitido. As tabelas e colunas novas são criadas/migradas aditivamente na inicialização.

Admins têm painel web/Android para revisão de jogos, denúncias, contas, eventos e classificação de conteúdo por plataforma. A categoria Android é armazenada no registro do jogo (`platform=android`) e filtrada pela API, não apenas pelo cliente.
