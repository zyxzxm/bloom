#define MyAppName "BLOOM"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "BLOOM"
#define MyAppExeName "BLOOM.exe"

[Setup]
AppId={{A7F4F683-784A-4C97-8D6F-7EBB1F1B10D3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BLOOM
DefaultGroupName=BLOOM
OutputDir=..\release
OutputBaseFilename=BLOOM-Setup
SetupIconFile=..\assets\bloom.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "..\dist\BLOOM.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\BLOOM"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\BLOOM"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir BLOOM"; Flags: postinstall nowait skipifsilent
