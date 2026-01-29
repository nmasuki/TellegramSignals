; Inno Setup Script for Telegram Signal Extractor
; Creates a self-extracting installer for Windows
;
; Requirements:
;   1. Run build_exe.py first to create dist/TelegramSignals/
;   2. Install Inno Setup from https://jrsoftware.org/isinfo.php
;   3. Compile this script with Inno Setup Compiler
;
; Command line: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

#define MyAppName "Telegram Signal Extractor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TelegramSignals"
#define MyAppURL "https://github.com/yourusername/TelegramSignals"
#define MyAppExeName "TelegramSignals.exe"

[Setup]
; App identity
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\installer
OutputBaseFilename=TelegramSignals_Setup_{#MyAppVersion}
SetupIconFile=..\src\gui\resources\icons\app.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Privileges (per-user install, no admin required)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Uninstaller
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start automatically with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Main application files from PyInstaller output
Source: "..\dist\TelegramSignals\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Config template
Source: "..\config\.env.example"; DestDir: "{app}\config"; Flags: ignoreversion; DestName: ".env.example"

[Dirs]
; Create writable directories
Name: "{app}\config"; Permissions: users-modify
Name: "{app}\output"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\sessions"; Permissions: users-modify

[Icons]
; Start menu
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Autostart entry (optional task)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "TelegramSignals"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Option to run app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if .env exists, prompt user to configure on first install
procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFile: string;
begin
  if CurStep = ssPostInstall then
  begin
    EnvFile := ExpandConstant('{app}\config\.env');
    if not FileExists(EnvFile) then
    begin
      MsgBox('Setup complete!' + #13#10 + #13#10 +
             'Before running the application, please:' + #13#10 +
             '1. Copy config\.env.example to config\.env' + #13#10 +
             '2. Edit .env with your Telegram API credentials' + #13#10 + #13#10 +
             'Get API credentials from: https://my.telegram.org',
             mbInformation, MB_OK);
    end;
  end;
end;

// Warn about existing sessions on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  SessionDir: string;
begin
  if CurUninstallStep = usUninstall then
  begin
    SessionDir := ExpandConstant('{app}\sessions');
    if DirExists(SessionDir) then
    begin
      if MsgBox('Do you want to keep your Telegram session files?' + #13#10 +
                '(If you reinstall, you won''t need to log in again)',
                mbConfirmation, MB_YESNO) = IDNO then
      begin
        DelTree(SessionDir, True, True, True);
      end;
    end;
  end;
end;
