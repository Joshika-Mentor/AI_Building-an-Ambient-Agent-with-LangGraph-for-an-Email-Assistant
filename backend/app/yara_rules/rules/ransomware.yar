/*
    ThreatLens AI - Ransomware Detection Rules
*/

rule Ransomware_File_Extensions
{
    meta:
        description = "Detects references to ransomware-associated file extensions"
        severity = "critical"
        category = "ransomware"

    strings:
        $ext1 = ".encrypted" ascii nocase
        $ext2 = ".locked" ascii nocase
        $ext3 = ".crypted" ascii nocase
        $ext4 = ".crypt" ascii nocase
        $ext5 = ".locky" ascii nocase
        $ext6 = ".cerber" ascii nocase
        $ext7 = ".zepto" ascii nocase
        $ext8 = ".wannacry" ascii nocase

    condition:
        2 of ($ext*)
}

rule Ransomware_Ransom_Note
{
    meta:
        description = "Detects common ransomware ransom note patterns"
        severity = "critical"
        category = "ransomware"

    strings:
        $note1 = "Your files have been encrypted" ascii nocase
        $note2 = "bitcoin" ascii nocase
        $note3 = "ransom" ascii nocase
        $note4 = "decrypt" ascii nocase
        $note5 = "pay" ascii nocase
        $note6 = "wallet" ascii nocase
        $note7 = "recover your files" ascii nocase
        $note8 = "send bitcoin" ascii nocase

    condition:
        3 of ($note*)
}

rule Ransomware_Crypto_APIs
{
    meta:
        description = "Detects use of cryptographic APIs commonly used by ransomware"
        severity = "high"
        category = "ransomware"

    strings:
        $crypto1 = "CryptEncrypt" ascii
        $crypto2 = "CryptGenKey" ascii
        $crypto3 = "CryptAcquireContext" ascii
        $crypto4 = "CryptImportKey" ascii
        $crypto5 = "BCryptEncrypt" ascii
        $file1 = "FindFirstFile" ascii
        $file2 = "FindNextFile" ascii
        $file3 = "MoveFileEx" ascii

    condition:
        uint16(0) == 0x5A4D and 2 of ($crypto*) and 1 of ($file*)
}
