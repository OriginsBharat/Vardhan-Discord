' This VBScript will run the start_world.bat file in a hidden window,
' ensuring the entire world starts silently in the background.
' The setup script will place a shortcut to this file in the Windows Startup folder.

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "start_world.bat", 0
Set WshShell = Nothing