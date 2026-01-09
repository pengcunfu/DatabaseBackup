; ===============================================
; Database Backup Tool - Inno Setup 安装脚本
; ===============================================
;
; 注意：以下版本信息由 build_installer.py 通过命令行参数传递
; 如果直接使用 ISCC.exe 编译，需要手动定义以下变量：
;   /dPRODUCT_VERSION, /dYEAR, /dAUTHOR, /dCOMPANY_NAME, /dPRODUCT_NAME, /dDESCRIPTION
;
; 示例：
;   ISCC.exe /dPRODUCT_VERSION="0.0.2" /dYEAR="2025" install.iss
; ===============================================

; ------------------- 配置区域 -------------------

; 默认值（仅当未通过命令行传递时使用）
#ifndef PRODUCT_VERSION
  #define PRODUCT_VERSION "0.0.2"
#endif

#ifndef YEAR
  #define YEAR "2025"
#endif

#ifndef AUTHOR
  #define AUTHOR "pengcunfu"
#endif

#ifndef PRODUCT_NAME
  #define PRODUCT_NAME "Database Backup Tool"
#endif

#ifndef COMPANY_NAME
  #define COMPANY_NAME "PyDatabaseBackup"
#endif

#ifndef DESCRIPTION
  #define DESCRIPTION "MySQL Database Backup and Synchronization Tool"
#endif

; 安装程序基本配置
#define INSTALLER_NAME "DatabaseBackup-Setup-" + PRODUCT_VERSION
#define MAIN_EXE_NAME "DatabaseBackup.exe"
#define PRODUCT_PUBLISHER COMPANY_NAME
#define PRODUCT_WEB_SITE "https://github.com/pengcunfu/DatabaseBackup"

; 源文件目录（编译后的程序）
; 注意：脚本在scripts目录，所以需要向上一级
#define SOURCE_DIR "..\dist\main.dist"

; ------------------------------------------------

[Setup]
; 安装程序基本设置
AppId={{A1B2C3D4-E5F6-4A5B-8C7D-9E0F1A2B3C4D}
AppName={#PRODUCT_NAME}
AppVersion={#PRODUCT_VERSION}
AppPublisher={#PRODUCT_PUBLISHER}
AppPublisherURL={#PRODUCT_WEB_SITE}
AppSupportURL={#PRODUCT_WEB_SITE}
AppUpdatesURL={#PRODUCT_WEB_SITE}
AppCopyright=Copyright (C) {#YEAR} {#AUTHOR}
VersionInfoVersion={#PRODUCT_VERSION}
VersionInfoCompany={#PRODUCT_PUBLISHER}
VersionInfoDescription={#DESCRIPTION}
VersionInfoCopyright=Copyright (C) {#YEAR} {#AUTHOR}
VersionInfoProductName={#PRODUCT_NAME}
VersionInfoProductVersion={#PRODUCT_VERSION}

; 默认安装目录
DefaultDirName={autopf}\{#COMPANY_NAME}
DefaultGroupName={#PRODUCT_NAME}

; 输出文件
OutputDir=..\output
OutputBaseFilename={#INSTALLER_NAME}

; 压缩设置
Compression=lzma2/max
SolidCompression=yes

; 安装程序外观
WizardStyle=modern
; 不指定自定义图片，使用默认图片
; WizardImageFile=compiler:WIZMODERNIMAGE.BMP
; WizardSmallImageFile=compiler:WIZMODERNSMALL.BMP
; SetupIconFile=resources\icon.ico

; 权限要求
PrivilegesRequired=admin
ChangesAssociations=yes
ChangesEnvironment=yes

; 其他设置
DisableDirPage=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableFinishedPage=no
AllowNoIcons=yes
AlwaysShowDirOnReadyPage=yes
AlwaysShowGroupOnReadyPage=yes

; 卸载设置
UninstallDisplayIcon={app}\{#MAIN_EXE_NAME}
UninstallFilesDir={app}\uninstall
AppendDefaultDirName=yes
AppendDefaultGroupName=yes

; ------------------- 语言设置 -------------------

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ------------------- 任务设置 -------------------

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; GroupDescription: "Additional icons:"; Flags: unchecked; OnlyBelowVersion: 6.1

; ------------------- 文件安装 -------------------

[Files]
; 安装主程序和所有依赖文件
Source: "{#SOURCE_DIR}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 注意：上面的标志说明：
; ignoreversion - 覆盖已存在的文件而不检查版本
; recursesubdirs - 递归复制所有子目录
; createallsubdirs - 在目标目录中创建所有源目录结构

; ------------------- 快捷方式 -------------------

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#PRODUCT_NAME}"; Filename: "{app}\{#MAIN_EXE_NAME}"; IconFilename: "{app}\{#MAIN_EXE_NAME}"; Comment: "{#DESCRIPTION}"
Name: "{group}\Uninstall {#PRODUCT_NAME}"; Filename: "{uninstallexe}"

; 桌面快捷方式（根据任务选择）
Name: "{autodesktop}\{#PRODUCT_NAME}"; Filename: "{app}\{#MAIN_EXE_NAME}"; Tasks: desktopicon; IconFilename: "{app}\{#MAIN_EXE_NAME}"; Comment: "{#DESCRIPTION}"

; 快速启动快捷方式（根据任务选择）
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#PRODUCT_NAME}"; Filename: "{app}\{#MAIN_EXE_NAME}"; Tasks: quicklaunchicon

; ------------------- 注册表设置 -------------------

[Registry]
; 在"添加/删除程序"中创建条目（额外信息）
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#COMPANY_NAME}"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\{#MAIN_EXE_NAME}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#COMPANY_NAME}"; ValueType: string; ValueName: "DisplayName"; ValueData: "{#PRODUCT_NAME}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#COMPANY_NAME}"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#PRODUCT_VERSION}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#COMPANY_NAME}"; ValueType: string; ValueName: "Publisher"; ValueData: "{#PRODUCT_PUBLISHER}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#COMPANY_NAME}"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "{#PRODUCT_WEB_SITE}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#COMPANY_NAME}"; ValueType: dword; ValueName: "NoModify"; ValueData: "1"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#COMPANY_NAME}"; ValueType: dword; ValueName: "NoRepair"; ValueData: "1"; Flags: uninsdeletekey

; 应用程序注册表项（保存配置）
Root: HKCU; Subkey: "Software\{#COMPANY_NAME}"; ValueType: string; ValueName: "Install_Dir"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#COMPANY_NAME}"; ValueType: string; ValueName: "Version"; ValueData: "{#PRODUCT_VERSION}"; Flags: uninsdeletekey

; ------------------- 运行设置 -------------------

[Run]
; 安装完成后运行程序（可选）
Filename: "{app}\{#MAIN_EXE_NAME}"; Description: "Launch {#PRODUCT_NAME}"; Flags: nowait postinstall skipifsilent

; ------------------- 卸载设置 -------------------

[UninstallDelete]
; 删除卸载目录
Type: filesandordirs; Name: "{app}\uninstall"

; ------------------- 安装程序代码 -------------------

[Code]
// 安装前检查
function InitializeSetup(): Boolean;
var
  PrevVersion: String;
begin
  Result := True;

  // 检查是否已经安装
  if RegQueryStringValue(HKCU, 'Software\{#COMPANY_NAME}', 'Install_Dir', PrevVersion) then
  begin
    if MsgBox('{#PRODUCT_NAME} is already installed.' + #13#10 + #13#10 +
              'Do you want to overwrite the installation?',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

// 安装完成后提示
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssDone then
  begin
    // 可以在这里添加额外的安装后操作
  end;
end;

// 卸载前确认
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('Are you sure you want to uninstall {#PRODUCT_NAME} and all its components?',
            mbConfirmation, MB_YESNO) = IDNO then
  begin
    Result := False;
  end;
end;

// 卸载完成后提示
procedure DeinitializeSetup();
begin
  // 安装向导关闭时的操作
end;

procedure DeinitializeUninstall();
begin
  // 卸载向导关闭时的操作
end;
