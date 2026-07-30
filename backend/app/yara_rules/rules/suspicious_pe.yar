/*
    ThreatLens AI - Suspicious PE Detection Rules
    Detects suspicious characteristics in PE (Portable Executable) files.
*/

rule Packed_UPX
{
    meta:
        description = "Detects UPX packed executables"
        severity = "medium"
        category = "packing"

    strings:
        $upx1 = "UPX0" ascii
        $upx2 = "UPX1" ascii
        $upx3 = "UPX!" ascii

    condition:
        uint16(0) == 0x5A4D and any of ($upx*)
}

rule Suspicious_PE_Imports
{
    meta:
        description = "Detects PE files with suspicious API imports commonly used by malware"
        severity = "high"
        category = "suspicious_imports"

    strings:
        $api1 = "VirtualAlloc" ascii
        $api2 = "VirtualProtect" ascii
        $api3 = "CreateRemoteThread" ascii
        $api4 = "WriteProcessMemory" ascii
        $api5 = "NtUnmapViewOfSection" ascii
        $api6 = "QueueUserAPC" ascii
        $api7 = "SetWindowsHookEx" ascii
        $api8 = "OpenProcess" ascii
        $api9 = "VirtualAllocEx" ascii

    condition:
        uint16(0) == 0x5A4D and 3 of ($api*)
}

rule Suspicious_PE_Section_Names
{
    meta:
        description = "Detects PE files with suspicious or non-standard section names"
        severity = "medium"
        category = "anomaly"

    strings:
        $sec1 = ".ndata" ascii
        $sec2 = ".enigma" ascii
        $sec3 = ".themida" ascii
        $sec4 = ".vmp0" ascii
        $sec5 = ".vmp1" ascii
        $sec6 = ".aspack" ascii
        $sec7 = ".adata" ascii
        $sec8 = ".packed" ascii

    condition:
        uint16(0) == 0x5A4D and any of ($sec*)
}

rule PE_With_Overlay
{
    meta:
        description = "Detects PE files with overlay data (appended data after PE structure)"
        severity = "low"
        category = "anomaly"

    strings:
        $mz = { 4D 5A }

    condition:
        $mz at 0 and filesize > 1MB
}
