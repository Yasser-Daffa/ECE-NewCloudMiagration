; ================================
; ECE Course Registration Installer
; ================================

[Setup]
AppName=ECE Course Registration
AppVersion=1.0.0
AppPublisher=Yasser
DefaultDirName={pf}\ECE Course Registration
DefaultGroupName=ECE Course Registration
OutputDir=installer
OutputBaseFilename=ECE_Course_Registration_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=app.ico

; Require admin rights to install
PrivilegesRequired=admin

; ================================
; FILES
; ================================
[Files]
; Main EXE
Source="dist\ECECourseRegistration.exe"; DestDir="{app}"; Flags: ignoreversion

; OPTIONAL: include icon
Source="app.ico"; DestDir="{app}"; Flags: ignoreversion

; OPTIONAL: include README
Source="README.md"; DestDir="{app}"; Flags: ignoreversion

; ================================
; SHORTCUTS
; ================================
[Icons]
Name="{autoprograms}\ECE Course Registration"; Filename="{app}\ECECourseRegistration.exe"
Name="{autodesktop}\ECE Course Registration"; Filename="{app}\ECECourseRegistration.exe"

; ================================
; UNINSTALL ENTRY
; ================================
[UninstallDelete]
Type: files; Name: "{app}\app.ico"
Type: files; Name: "{app}\README.md"
