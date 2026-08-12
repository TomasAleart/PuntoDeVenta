; ===========================================
; INSTALADOR DEL SISTEMA - BLINDADO
; Minimarket V&E - Nivel 1 (Actualizado 2026)
; ===========================================

[Setup]
AppName=Minimarket V&E
AppVersion=1.0
DefaultDirName={pf}\MinimarketVE
DefaultGroupName=Minimarket V&E
OutputBaseFilename=MinimarketVE_Setup
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes

[Files]
; --- 1. Copiar el ejecutable principal ---
Source: "C:\Users\usuario\Documents\TomasAleart\Minimarket\SistemaMinimarket\dist\MinimarketVE\MinimarketVE.exe"; DestDir: "{app}"; Flags: ignoreversion

; --- 2. Copiar absolutamente todo el contenido generado (incluyendo la BD de plantilla que encuentre PyInstaller) ---
Source: "C:\Users\usuario\Documents\TomasAleart\Minimarket\SistemaMinimarket\dist\MinimarketVE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Minimarket V&E"; Filename: "{app}\MinimarketVE.exe"
Name: "{commondesktop}\Minimarket V&E"; Filename: "{app}\MinimarketVE.exe"

[Run]
Filename: "{app}\MinimarketVE.exe"; Description: "Iniciar Minimarket V&E"; Flags: nowait postinstall skipifsilent