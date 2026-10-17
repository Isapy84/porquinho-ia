Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonwPath = currentDir & "\.venv\Scripts\pythonw.exe"
botPath = currentDir & "\bot.py"

If Not fso.FileExists(currentDir & "\.env") Then
    MsgBox "Arquivo .env nao encontrado! Crie o arquivo .env com suas chaves antes de iniciar.", vbCritical, "Porquinho IA"
    WScript.Quit
End If

WshShell.CurrentDirectory = currentDir
WshShell.Run """" & pythonwPath & """ """ & botPath & """", 0, False
MsgBox "Porquinho IA iniciado em segundo plano com sucesso! 🐷" & vbCrLf & "O bot continuará rodando mesmo com a IDE fechada.", vbInformation, "Porquinho IA"
