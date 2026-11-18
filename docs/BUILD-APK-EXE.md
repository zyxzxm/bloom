# Tutorial: compilar o BLOOM para Windows (.exe) e Android (.apk)

O repositório tem dois clientes: o desktop Python/Tkinter e a experiência web em `web/`, apoiada pela API FastAPI. Este tutorial ensina a compilar localmente os dois aplicativos. O ZIP do código-fonte contém fontes; os arquivos finais são gerados pelos passos abaixo.

## 1. Compilar o EXE no Windows

A compilação do desktop deve ser feita no Windows. Instale Python 3.12 em [python.org](https://www.python.org/downloads/windows/) e marque **Add python.exe to PATH**. Baixe e extraia o projeto (ou clone o repositório) em uma pasta, por exemplo `C:\BLOOM`. Abra PowerShell nessa pasta e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
$env:BLOOM_API_URL = 'https://bloom-world.onrender.com'
.\build_windows.ps1
```

O script cria o ambiente isolado `.venv-build`, instala `pywebview` e as dependências e verifica a rota `/health` da API antes de compilar. O EXE incorpora toda a pasta `web/` (HTML, CSS, JavaScript, imagens e trilha), abre a nova experiência em uma janela WebView e serve os arquivos localmente. O runtime WebView2 do Microsoft Edge precisa estar presente no Windows (já vem instalado no Windows 11 e em muitos Windows 10 atualizados; o build não inclui o runtime). O executável sai em `release\BLOOM.exe`. Se Inno Setup 6 estiver instalado, também será produzido `release\BLOOM-Setup.exe`. O computador que vai apenas executar o app não precisa ter Python.

Para usar outra API, altere `BLOOM_API_URL` para a URL pública HTTPS antes do comando. Nunca use `localhost` em um executável destinado a outras pessoas. O EXE resultante não inclui certificado de publisher; o Windows SmartScreen pode exibir um aviso.

## 2. Compilar o APK no Windows com Android Studio

O APK Android contém a interface web do projeto como arquivos locais e a abre em uma WebView. Assim, a tela principal não depende da página raiz no servidor. Login, comunidade, uploads e outros recursos de servidor precisam de internet e da API `https://bloom-world.onrender.com` disponível. O app usa HTTPS, `WebViewAssetLoader` em origem segura, JavaScript e armazenamento DOM. O CORS da API foi verificado para a origem do WebView.

1. Instale o **Android Studio**. No **SDK Manager**, instale **Android SDK Platform 35** e **Android SDK Build-Tools 35**. O Android Studio inclui um JDK; se precisar configurar um, use JDK 17 ou posterior compatível.
2. Extraia o projeto e abra no Android Studio a pasta `android/` (a que contém `settings.gradle`). Aguarde a sincronização inicial do Gradle; o **Gradle Wrapper** incluído baixa a versão 8.9 automaticamente.
3. Escolha **Build > Build Bundle(s) / APK(s) > Build APK(s)**. O Gradle sincroniza `web/` para os assets automaticamente durante o build. Alternativamente, pelo PowerShell na raiz do repositório:

```powershell
.\android\gradlew.bat -p android assembleDebug
```

O arquivo gerado fica em `android\app\build\outputs\apk\debug\app-debug.apk`. No macOS/Linux, use `./android/gradlew -p android assembleDebug`.

4. Para testar, instale o APK debug no Android (autorize a instalação da origem escolhida) ou use **Run** com um emulador/celular conectado. Confira abertura do jardim, conexão com a API, login, feed, chat, áudio e links externos. Se a hospedagem estiver indisponível, os recursos que dependem da API não funcionarão.

O APK `debug` é próprio para instalar e testar. Para distribuição pública/Play Store, configure uma assinatura `release` e um keystore seu, protegido e fora do repositório. Sem a mesma chave, não será possível assinar atualizações compatíveis do mesmo app. Consulte [assinar um app Android](https://developer.android.com/studio/publish/app-signing) e a documentação de [WebView Android](https://developer.android.com/develop/ui/views/layout/webapps/webview).

## 3. Compilação alternativa pelo GitHub Actions

O workflow **Build BLOOM APK and EXE** também compila os dois artefatos em runners Linux/Android e Windows. Após enviar as alterações ao GitHub, abra **Actions**, selecione uma execução bem-sucedida e baixe `BLOOM-Android-APK` e `BLOOM-Windows-EXE`. É uma alternativa remota; para compilar no seu próprio computador, siga as seções 1 e 2. Os artifacts do Actions expiram após 14 dias.
