!macro NSIS_HOOK_PREINSTALL
  StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\ZZZ Bot"
!macroend

!macro NSIS_HOOK_POSTINSTALL
  Delete "$INSTDIR\\zzz-bot.exe"
!macroend
