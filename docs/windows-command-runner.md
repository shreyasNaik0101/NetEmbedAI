# Working command route on this Windows host

On 6 November 2026 the automatic PowerShell launcher repeatedly failed before
executing a command:

```text
CreateProcessAsUserW failed: 5 (Access is denied.)
C:\Users\shrey\AppData\Local\Microsoft\WindowsApps\pwsh.exe
```

The local logs show intermittent failures with this path on previous dates too.
The global configuration currently selects the `unelevated` Windows sandbox;
changing it was unnecessary. The exact underlying reason the Store launcher is
denied is unconfirmed. A full native PowerShell path in the tool's `shell`
argument was still resolved to that automatic Store launcher.

## Verified session workaround

Use the command tool with:

```json
{"shell":"C:\\Windows\\System32\\cmd.exe","login":false,"tty":false}
```

Set `workdir` to the project and run ordinary Git/Python commands directly.
For PowerShell tasks, call the built-in executable explicitly from this working
`cmd.exe` route:

```text
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -NonInteractive -Command Get-Date
```

Use `-File` for a saved PowerShell script to avoid nested quoting. Keep file
operations within the intended workspace and retain the active permission
profile. This route does not change Windows ACLs, security settings, sandbox
mode, user accounts or the default shell.

Successful checks: `cmd.exe` echo, native PowerShell `Get-Date`, Python3.11.9,
Git status/revision, the real frozen-model comparison and its independent audit.
Both normal piped and PTY `cmd.exe` launches work. The default Store PowerShell
route still fails, so this is a verified execution workaround, not a repaired
global PowerShell installation. No further manual user command was needed for
the comparison once this route was found.

Local verification receipt: `experiments/terminal-recovery-20261106/report.json`,
SHA-256 `4f6367e135d4492d683ec5b2dac0597271a3fe6280c04fc1b1292dba05639c2a`.
