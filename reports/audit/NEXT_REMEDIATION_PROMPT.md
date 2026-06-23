# Next Remediation Prompt

Source report: reports\audit\AUDIT_REPORT_20260622_030840.md
Latest report pointer: reports\audit\AUDIT_REPORT_LATEST.md
Selected batch prompt path: reports\audit\NEXT_REMEDIATION_PROMPT.md
Selected batch: Time HUD plumbing
Severity: Low

Implement exactly one small, testable improvement: wire the existing game-time string into the HUD so players can see it. Keep the change limited to the current time/HUD path, preserve user work, do not copy protected content, and do not commit. Add the smallest tests needed to prove the time display path still round-trips cleanly.
