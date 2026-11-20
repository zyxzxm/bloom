# BLOOM — entregas e critérios

## 1. Preservação do projeto original
- [x] Analisar o código original disponível no ZIP e no repositório BLOOM do GitHub.
- [x] Preservar o projeto original e seu histórico.
- [x] Analisar o código original, preservar o que funciona e melhorar o que for necessário.
- [x] Desktop: manter o cliente Python/Tkinter, BLOOM MAKER, BLOOM SAFE e as funcionalidades locais existentes.

## 2. Identidade e experiência visual
- [x] Aplicar Frutiger Aero, Green Aero, Aqua Aero e Technozen. Utilizar oceanos, natureza, céus, nuvens, esferas de vidro, transparências, reflexos, efeitos 3D, gradientes vibrantes, partículas e animações. Interface futurista, colorida, divertida e sofisticada, sem minimalismo, cinza ou aparência genérica.
- [x] Criar experiência imersiva com transições fluidas, microinterações, efeitos visuais, animações ambientais e detalhes surpreendentes.
- [x] Pesquisar referências visuais e incorporar imagens de qualidade cujas licenças permitem o uso pretendido.
- [x] Créditos de autoria exibem exclusivamente: `BLOOM — Created by ZYXZXM.` Não atribuir BLOOM a IA, Manus ou ChatGPT.

## 3. Música ambiente
- [x] Pesquisar músicas ambientais Frutiger Aero, Aqua Aero e Green Aero; incorporar somente faixas com licenças compatíveis.
- [x] Implementar reprodução, pausa e controle de volume.
- [x] Registrar as licenças dos ativos incorporados em documentação do repositório sem ampliar o crédito exibido no produto.

## 4. Desktop e mobile responsivos
- [x] Criar versões completas e responsivas para computador e celular.
- [x] Mobile preserva identidade visual, funcionalidades e qualidade, com navegação otimizada para toque.

## 5. Funcionalidades reais
- [x] Todas as funcionalidades web apresentadas devem funcionar de verdade; evitar botões decorativos ou recursos falsos.
- [x] Permitir iniciar e usar conversas de qualquer tela/projeto; mensagens persistidas pela API real.
- [x] Manter as capacidades locais de instalação/Maker/segurança no cliente desktop quando a API não oferecer equivalente browser.

## 6. Redes sociais
- [x] Link clicável de itch.io: https://zyx4415.itch.io/bloom
- [x] Link clicável de TikTok: https://www.tiktok.com/@bloom.games.and.c
- [x] Exibir imagens oficiais das marcas nas ações sociais.

## 7. GitHub, documentação e publicação
- [x] Trabalhar diretamente no repositório BLOOM em GitHub.
- [x] Publicar alterações de código, imagens, áudio e documentação no repositório GitHub; atualizar README e organizar commits.
- [x] Preservar commits e histórico local existentes; nenhuma alteração destrutiva/force-push foi feita.
- [x] Confirmar a publicação do commit `8588a46` na branch `main`.

## 8. Validação e desempenho
- [x] Executar o projeto; testar funcionalidades, links, áudio, navegação, desktop e mobile; corrigir erros e otimizar.


## 9. Logo do aplicativo Android
- [x] Adicionar logo oficial ao aplicativo Android, utilizando a mesma identidade visual da versão para computador.
- [x] Configurar o ícone exibido na tela inicial, na lista de aplicativos e nas áreas do Android, com ícones adaptativos e recursos nas densidades mdpi a xxxhdpi.
- [x] Compilar e conferir o APK debug que contém os novos ícones.

## 10. Sistema completo de administração (ADMIN)
- [x] Autorizar a conta do criador pelo ID numérico confiável no servidor, sem atribuir privilégio com base em campos de perfil/username; rejeitar autoelevação de usuário comum.
- [x] Implementar checagens administrativas no backend e uma interface funcional compartilhada por computador e Android.
- [x] Disponibilizar ações administrativas para criar, editar e remover eventos; revisar, aprovar ou rejeitar jogos enviados; remover jogos/conteúdos inadequados; banir, desbanir e suspender contas; editar perfis; alterar a plataforma/categoria de jogos; e gerenciar denúncias.
- [x] Testar acesso negado a usuário comum, ações de evento, contas suspensas/banidas, filtros de plataforma Android, remoção de posts/comentários/mensagens e persistência da autoridade após nova autenticação.
- [x] Provisionar no Render `BLOOM_OWNER_USER_ID=1` (ID público confirmado da conta `@ZYXZXM`) e implantar o commit `8588a46`; `/health` retornou 200 e `/api/admin/summary` sem autenticação retornou 401.
- [ ] Confirmar a interface admin autenticada na produção com a conta BLOOM owner e uma conta comum; o navegador estava sem sessão BLOOM autenticada.

## 11. Proteção de nomes de usuário (@)
- [x] Garantir username único no servidor, normalizado em minúsculas, com conflito por duplicidade respondendo HTTP 409 e restrição única persistida no banco para corridas concorrentes.
- [x] Ao trocar de @, verificar disponibilidade e impedir assumir @ reservado ou em uso; reservar `@ZYXZXM` para a conta oficial identificada no servidor.
- [x] Testar variantes de caixa, reserva do nome e dois cadastros simultâneos concorrendo pelo mesmo username (exatamente uma conta é criada).

## 12. Interface totalmente responsiva no Android
- [x] Adaptar a interface para celulares e tablets, mantendo a identidade BLOOM, navegação por toque, áreas seguras, rolagem e layouts para telas estreitas e paisagem.
- [x] Capturar e inspecionar viewports 390×844, 844×390 e desktop 1365×900; não foram observados elementos móveis cortados ou sobrepostos nas capturas.
- [ ] Executar a interface dentro de emulador ou aparelho Android real; não havia AVD/emulador configurado nesta sessão.

## 13. Reprodução automática da música de fundo
- [x] Tentar iniciar a música automaticamente ao abrir, sem exigir tela/botão Play; se a política do navegador bloquear, instalar fallback de início no primeiro gesto.
- [x] Manter o elemento de áudio durante a navegação SPA e lembrar volume, atmosfera musical e opção de silenciar.
- [x] Manter controles de pausar/retomar, volume e mute; ajustar a configuração WebView Android para permitir playback sem gesto obrigatório.
- [ ] Validar reprodução/autoplay e fallback em hardware Android e navegador desktop real; os testes atuais cobrem código e inspeção local, não saída de áudio física.

## 14. Nova categoria Android no Explorar
- [x] Adicionar a categoria Android junto das demais, com identificação visual própria e consulta filtrada ao backend para conteúdo Android ou `all`.
- [x] Integrar seleção da plataforma ao envio e à administração dos jogos; confirmar armazenamento, edição administrativa e filtragem Android nos testes da API.
- [x] Permitir abrir e visualizar os jogos normalmente na interface web, usada também pelo WebView Android.

## 15. Verificação final e entrega
- [x] Implementar as alterações diretamente no projeto existente, preservando os recursos e sem substituir integrações por placeholders.
- [x] Suíte integral: 17 testes passaram; compilação Python, `node --check` e `git diff --check` passaram.
- [x] Gerar APK debug Android atualizado; copiar/entregar o artefato após conferir integridade.
- [x] Publicar o código/documentação no GitHub; Render implantou com sucesso o commit `8588a46`.
- [ ] Conferir privilégios owner e usuário comum na produção após configurar o ID; distinguir esse provisionamento de testes locais.
- [ ] Concluir validações que exigem dispositivo/saída de áudio real, ou documentar explicitamente a limitação se não houver hardware disponível.
