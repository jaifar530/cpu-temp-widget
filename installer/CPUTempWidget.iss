; CPU Temperature Widget - Inno Setup Installer Script
; Download Inno Setup from: https://jrsoftware.org/isinfo.php

#define MyAppName "CPU Temperature Widget"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Virtual Platforms LLC"
#define MyAppURL "https://github.com/jaifar530/cpu-temp-widget"
#define MyAppExeName "CPUTempWidget.exe"

[Setup]
; Unique identifier for this application
AppId={{A7B8C9D0-E1F2-4A5B-8C9D-0E1F2A5B8C9D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output settings
OutputDir=..\installer_output
OutputBaseFilename=CPUTempWidget_Setup_{#MyAppVersion}
; Visual settings
SetupIconFile=..\resources\icon.ico
WizardStyle=modern
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Privileges - require admin for better hardware access
PrivilegesRequired=admin
; Uninstaller
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Minimum Windows version
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start automatically with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Add to startup if selected
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "CPUTempWidget"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Option to run after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop the app before uninstalling
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden

[UninstallDelete]
; Clean up config folder
Type: filesandordirs; Name: "{userappdata}\CPUTempWidget"

[Code]
// Close the application if it's running before installation
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Try to close the application gracefully
  Exec('taskkill', '/F /IM CPUTempWidget.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;
