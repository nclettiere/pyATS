@echo off

rem This Script will generate the blender addon on your desktop.
rem Ensure that you have 7zip installed on Program Files

set ADDON="%USERPROFILE%\Desktop\pyats_addon.zip"

del %ADDON% >nul 2>&1

"C:\Program Files\7-Zip\7z.exe" a %ADDON% src/
"C:\Program Files\7-Zip\7z.exe" rn %ADDON% src\ pyATS\
