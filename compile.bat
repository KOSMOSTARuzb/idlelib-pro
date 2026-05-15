@ECHO OFF
echo Compiling...
pyinstaller --onefile --add-data K_change_assets:K_change_assets --exclude-module idlelib installer.py
move .\dist\installer.exe setup.exe
rmdir dist /S /Q
echo DONE
pause