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
; Neu ban cai cu (GoogleMapsReviewBot.exe) van dang chay/bi treo, Windows se khoa
; file va Setup se hoi "Try again / Ignore / Cancel" - neu nguoi dung khong xu ly
; kip (hoac cai o che do im lang), toan bo qua trinh cai se bi ROLLBACK HET, khien
; tool_config.json (va moi file khac) khong duoc cap nhat du ban moi da dung.
; Chu dong taskkill ban cu trong InitializeSetup() (xem [Code]) truoc khi Setup
; kip hoi, nen khong can dua vao RestartManager/CloseApplications nua.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\GoogleMapsReviewBot.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Danh sach tai khoan Google mac dinh. KHONG dung "onlyifdoesntexist" don thuan,
; vi flag do se BO QUA viec ghi file moi neu may da co BAT KY tool_config.json
; nao tu truoc - ke ca file RONG/hong tu 1 lan cai/test cu - khien tai khoan
; mac dinh khong bao gio duoc ghi vao du cai ban moi nhat. Thay vao do, dung
; ham Check (xem [Code] ben duoi): chi giu file cu neu no THAT SU co tai khoan
; ben trong, con neu rong thi ghi de bang file mac dinh moi.
Source: "installer_default_tool_config.json"; DestDir: "{app}"; DestName: "tool_config.json"; Check: ShouldInstallDefaultConfig; Flags: ignoreversion

[Dirs]
Name: "{app}\profiles"
Name: "{app}\images"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Chu dong dong moi ban GoogleMapsReviewBot.exe con dang chay (ke ca tien
  // trinh bi treo tu lan cai/dung truoc), truoc khi Setup kip kiem tra file
  // dang bi khoa. Neu khong lam buoc nay, Setup co the phai hoi nguoi dung
  // (Try again/Ignore/Cancel) hoac tu rollback toan bo qua trinh cai neu
  // khong dong duoc ung dung, khien khong file nao duoc cap nhat.
  Exec('taskkill.exe', '/F /IM GoogleMapsReviewBot.exe /T', '', SW_HIDE,
       ewWaitUntilTerminated, ResultCode);
  Result := True;
end;

function ShouldInstallDefaultConfig(): Boolean;
var
  ExistingPath: String;
  RawContent: AnsiString;
  Content: String;
  FoundPos: Integer;
begin
  ExistingPath := ExpandConstant('{app}\tool_config.json');
  if not FileExists(ExistingPath) then
  begin
    Result := True; // chua cai lan nao -> ghi file mac dinh
    Log('ShouldInstallDefaultConfig: chua co file -> ghi mac dinh');
    exit;
  end;
  // Da co file: chi ghi de neu file do RONG tai khoan (khong chua "email" nao
  // trong google_accounts). Neu nguoi dung da tung dang nhap/them tai khoan
  // that (co it nhat 1 "email"), giu nguyen file cua ho, khong dong vao.
  if LoadStringFromFile(ExistingPath, RawContent) then
  begin
    Content := String(RawContent);
    FoundPos := Pos('"email"', Content);
    Log('ShouldInstallDefaultConfig: doc duoc ' + IntToStr(Length(Content)) +
        ' ky tu, vi tri "email" = ' + IntToStr(FoundPos));
    Result := (FoundPos = 0);
  end
  else
  begin
    Log('ShouldInstallDefaultConfig: LoadStringFromFile that bai -> giu file cu');
    Result := False;
  end;
end;
