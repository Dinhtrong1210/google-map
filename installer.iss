; Inno Setup script - dong goi GoogleMapsReviewBot.exe thanh mot installer
; chuan Windows: co man hinh chon "Tao icon Desktop?", tao Start Menu,
; va uninstaller. Chay: ISCC.exe installer.iss (sau khi da build exe qua PyInstaller).

#define MyAppName "Google Maps Review Bot"
#define MyAppVersion "4.0.0"
#define MyAppPublisher "DJ Media"
#define MyAppURL "https://phamhuudungmedia.vn"
#define MyAppExeName "GoogleMapsReviewBot.exe"

[Setup]
AppId={{B8A1F1E4-6C3D-4A2E-9F5B-3D8C7E2A1F90}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
; Cai vao thu muc rieng cua user (khong can quyen Admin), vi tool ghi
; config/profile ngay canh file exe.
DefaultDirName={userpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=GoogleMapsReviewBot_Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\GoogleMapsReviewBot.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Danh sach tai khoan Google mac dinh - chi ghi khi cai moi (onlyifdoesntexist),
; khong ghi de neu nguoi dung da co tool_config.json tu truoc (vd: cai lai/nang cap
; ban da tung dung, da tu them/xoa tai khoan rieng).
Source: "installer_default_tool_config.json"; DestDir: "{app}"; DestName: "tool_config.json"; Flags: onlyifdoesntexist

[Dirs]
Name: "{app}\profiles"
Name: "{app}\images"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
