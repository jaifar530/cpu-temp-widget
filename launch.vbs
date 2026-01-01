' Silent launcher for CPU Temperature Widget
' This script runs the Python app without showing a console window

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Find Python executable (try pythonw first, then python)
pythonPath = ""

' Try common Python locations
pythonPaths = Array( _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python314\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python313\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python310\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Python\pythoncore-3.14-64\pythonw.exe", _
    "C:\Python314\pythonw.exe", _
    "C:\Python313\pythonw.exe", _
    "C:\Python312\pythonw.exe" _
)

For Each p In pythonPaths
    If fso.FileExists(p) Then
        pythonPath = p
        Exit For
    End If
Next

' If not found, try to find pythonw in PATH
If pythonPath = "" Then
    On Error Resume Next
    Set exec = WshShell.Exec("where pythonw.exe")
    If Err.Number = 0 Then
        pythonPath = Trim(exec.StdOut.ReadLine())
    End If
    On Error GoTo 0
End If

' Fall back to python.exe if pythonw not found
If pythonPath = "" Or Not fso.FileExists(pythonPath) Then
    On Error Resume Next
    Set exec = WshShell.Exec("where python.exe")
    If Err.Number = 0 Then
        pythonPath = Trim(exec.StdOut.ReadLine())
    End If
    On Error GoTo 0
End If

' Run the script
If pythonPath <> "" And fso.FileExists(pythonPath) Then
    mainScript = scriptDir & "\main.py"
    If fso.FileExists(mainScript) Then
        WshShell.Run """" & pythonPath & """ """ & mainScript & """", 0, False
    End If
End If
