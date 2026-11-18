# Compilar e publicar o BLOOM

Este ZIP/repositório é o **código-fonte**. Ele não contém APK ou EXE já compilados. Para gerar os aplicativos no seu computador, siga o [tutorial completo de build do APK e do EXE](docs/BUILD-APK-EXE.md).

## Gerar o EXE no Windows

Instale Python 3.12, extraia o projeto, abra PowerShell na pasta do repositório e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
$env:BLOOM_API_URL = 'https://bloom-world.onrender.com'
.\build_windows.ps1
```

O resultado fica em `release\BLOOM.exe`. Com Inno Setup 6 instalado, o script também gera `release\BLOOM-Setup.exe`.

## Gerar o APK com Android Studio

Instale Android Studio e Android SDK Platform 35. Abra a pasta `android/` do projeto e aguarde a sincronização do Gradle. Escolha **Build > Build Bundle(s) / APK(s) > Build APK(s)**. A interface de `web/` é copiada para o APK automaticamente. O mesmo build pode ser iniciado na raiz do projeto pelo PowerShell:

```powershell
.\android\gradlew.bat -p android assembleDebug
```

O APK de teste será `android\app\build\outputs\apk\debug\app-debug.apk`. Esse app inclui a interface web, mas precisa de internet para acessar a API hospedada. Para publicar na Play Store, gere uma versão `release` e assine com seu próprio keystore, que deve ficar privado.

## Usar builds do GitHub Actions (opcional)

O workflow **Build BLOOM APK and EXE** também pode compilar os dois itens remotamente. Após enviar o projeto ao GitHub, abra **Actions**, acesse a execução concluída e baixe os artifacts `BLOOM-Android-APK` e `BLOOM-Windows-EXE`. O build local continua sendo a opção explicada acima.
