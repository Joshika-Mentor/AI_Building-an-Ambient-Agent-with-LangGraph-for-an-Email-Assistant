/*
    ThreatLens AI - Trojan Detection Rules
*/

rule Trojan_Keylogger
{
    meta:
        description = "Detects potential keylogger functionality"
        severity = "critical"
        category = "trojan"

    strings:
        $key1 = "GetAsyncKeyState" ascii
        $key2 = "GetKeyState" ascii
        $key3 = "SetWindowsHookEx" ascii
        $key4 = "GetForegroundWindow" ascii
        $key5 = "GetWindowText" ascii
        $key6 = "keylog" ascii nocase

    condition:
        uint16(0) == 0x5A4D and 3 of ($key*)
}

rule Trojan_Process_Injection
{
    meta:
        description = "Detects process injection techniques"
        severity = "critical"
        category = "trojan"

    strings:
        $inj1 = "CreateRemoteThread" ascii
        $inj2 = "VirtualAllocEx" ascii
        $inj3 = "WriteProcessMemory" ascii
        $inj4 = "OpenProcess" ascii
        $inj5 = "NtCreateThreadEx" ascii
        $inj6 = "RtlCreateUserThread" ascii

    condition:
        uint16(0) == 0x5A4D and 3 of ($inj*)
}

rule Trojan_Data_Exfiltration
{
    meta:
        description = "Detects potential data exfiltration behavior"
        severity = "high"
        category = "trojan"

    strings:
        $exf1 = "FtpPutFile" ascii
        $exf2 = "HttpSendRequest" ascii
        $exf3 = "InternetWriteFile" ascii
        $exf4 = "smtp" ascii nocase
        $exf5 = "upload" ascii nocase
        $clip1 = "GetClipboardData" ascii
        $screen1 = "BitBlt" ascii
        $screen2 = "GetDC" ascii

    condition:
        uint16(0) == 0x5A4D and (2 of ($exf*) or (1 of ($clip*) and 1 of ($screen*)))
}
