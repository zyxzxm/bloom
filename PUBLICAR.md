# Publicar o BLOOM — guia simples

## Para você (uma vez por versão)

O `.exe` de Windows precisa ser compilado em **um PC Windows**. Este ambiente de trabalho é Linux, então não consigo gerar um `.exe` Windows daqui. O projeto já contém o script para você gerar o instalador no Windows.

### Antes de compilar

1. Tenha o BLOOM WORLD publicado em um endereço HTTPS que não dependa do seu PC, por exemplo `https://api.seudominio.com`. O instalador pergunta essa URL e testa `/health`. Sem backend online, login, catálogo e comunidade não podem funcionar para os jogadores. Para configurar hospedagem, siga a seção **Implantar a API** do `README.md`.
2. No PC de compilação, instale **Python 3.12** e **Inno Setup 6**. Python é usado só para compilar no seu PC; Inno Setup empacota o instalador.
3. Descompacte a pasta `bloom` no Windows. Clique com o botão direito em `build_windows.ps1` e escolha **Executar com PowerShell**, ou abra PowerShell na pasta e rode:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

O script cria sozinho um ambiente de build isolado, instala dependências de compilação, confirma que a API responde e produz:

```text
release\BLOOM-Setup.exe
```

Se o Windows perguntar, permita a execução do seu próprio script. Se o Inno Setup não estiver instalado, o script ainda gera `release\BLOOM.exe`; instale Inno Setup 6 para o instalador com atalho e desinstalação.

Antes de disponibilizar ao público, instale e teste `BLOOM-Setup.exe` num Windows 10/11 limpo, idealmente numa máquina virtual. Confira instalação, inicialização, cadastro, catálogo e download. Publique o instalador por HTTPS e compartilhe o hash SHA-256 por um canal confiável.

## Para o jogador

O jogador **não instala Python**, não abre terminal, não configura a URL da API e não precisa ver código. Ele só:

1. Baixa `BLOOM-Setup.exe` do seu site.
2. Abre o instalador e clica em **Avançar/Instalar**.
3. Abre o BLOOM pelo atalho.
4. Cria uma conta para usar a comunidade/loja.

A instalação ocorre no perfil do próprio usuário. Os dados ficam em `%APPDATA%\BLOOM`. O servidor online fica separado na nuvem.

## Limite importante

O instalador client só funciona com serviços online se você já tiver colocado o BLOOM WORLD no ar e usar a URL real dele ao compilar. Eu não publiquei o backend por você: isso exige uma conta/servidor externo. Hospedar e compilar são dois passos diferentes. Não distribua uma build apontada a um endereço de exemplo ou localhost.
