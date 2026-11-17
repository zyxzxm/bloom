# Compilar o instalador do BLOOM — guia simples

Este pacote contém o código atualizado do cliente. Para esta compilação, use o arquivo `BLOOM-Windows-build-source.zip` fornecido nesta conversa; não precisa baixar Git nem clonar o repositório.

## 1. Prepare o PC que vai compilar

Instale **Python 3.12** e **Inno Setup 6** no Windows. Python é necessário apenas no PC que cria o instalador; o jogador não precisa de Python. No instalador do Python, marque **Add python.exe to PATH**.

## 2. Extraia o projeto

1. Baixe `BLOOM-Windows-build-source.zip` pelo link desta conversa.
2. No Explorador de Arquivos, clique com o botão direito no ZIP e escolha **Extrair Tudo**.
3. Abra a pasta extraída e confirme que nela aparecem `build_windows.ps1`, `requirements-client.txt`, `bloom_app` e `installer`.

## 3. Gere o instalador

Dentro da pasta extraída, clique na barra de endereço do Explorador de Arquivos, digite `powershell` e pressione **Enter**. Na janela do PowerShell, execute estes comandos, um por vez:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

A primeira linha só permite executar o script nesta janela; não altera permanentemente a segurança do Windows.

Quando o script perguntar a URL HTTPS da API, pressione **Enter** para aceitar o padrão `https://bloom-world.onrender.com`. O script verifica a API, instala as ferramentas de build no ambiente isolado `.venv-build` e compila o cliente.

## 4. Aguarde e encontre o instalador

O BLOOM WORLD usa o plano gratuito do Render. Depois de um período sem uso, a API pode “dormir” e a primeira conexão pode levar aproximadamente **50 segundos** para acordar. Deixe o PowerShell aberto: o script tenta novamente enquanto o serviço inicia. Se todas as tentativas falharem, abra `https://bloom-world.onrender.com/health` no navegador, espere aparecer `"status":"ok"` e execute o script novamente.

Com o Inno Setup 6 instalado, o arquivo final estará em:

```text
release\BLOOM-Setup.exe
```

Se o Inno Setup não estiver instalado, o script pode produzir somente `release\BLOOM.exe`. Instale o Inno Setup 6 e rode o script novamente para gerar o instalador com atalho e desinstalação.

## Para os jogadores

Publique e distribua somente `BLOOM-Setup.exe`. Quem jogar baixa, instala e abre o BLOOM pelo atalho; não precisa instalar Python, Git, PowerShell ou configurar a URL da API. O servidor já está hospedado separadamente; não distribua um `BLOOM-Server.exe`.

**Nota sobre o GitHub:** a cópia `main` do repositório ainda não recebeu este commit, porque o envio foi recusado pela permissão de gravação do conector. Use o ZIP desta conversa para compilar agora; ele contém as alterações testadas.
