"""
ThreatLens AI - File Utilities
File hashing, type detection, and string extraction.
"""

import hashlib
import os
import re
import uuid
import aiofiles
from typing import Tuple, List, Optional


async def compute_hashes(file_path: str) -> Tuple[str, str]:
    """Compute MD5 and SHA-256 hashes of a file."""
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(8192):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

    return md5_hash.hexdigest(), sha256_hash.hexdigest()


def detect_file_type(file_path: str) -> Tuple[str, str]:
    """
    Detect file type using magic bytes.
    Returns (file_type, mime_type).
    """
    MAGIC_BYTES = {
        b'\x4d\x5a': ('PE Executable', 'application/x-dosexec'),
        b'\x7f\x45\x4c\x46': ('ELF Executable', 'application/x-elf'),
        b'\x50\x4b\x03\x04': ('ZIP Archive', 'application/zip'),
        b'\x25\x50\x44\x46': ('PDF Document', 'application/pdf'),
        b'\xd0\xcf\x11\xe0': ('MS Office Document', 'application/msword'),
        b'\x52\x61\x72\x21': ('RAR Archive', 'application/x-rar-compressed'),
        b'\x1f\x8b': ('GZIP Archive', 'application/gzip'),
        b'\x89\x50\x4e\x47': ('PNG Image', 'image/png'),
        b'\xff\xd8\xff': ('JPEG Image', 'image/jpeg'),
    }

    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)

        for magic, (file_type, mime_type) in MAGIC_BYTES.items():
            if header[:len(magic)] == magic:
                return file_type, mime_type

        # Fallback: check extension
        ext = os.path.splitext(file_path)[1].lower()
        ext_map = {
            '.exe': ('PE Executable', 'application/x-dosexec'),
            '.dll': ('PE DLL', 'application/x-dosexec'),
            '.pdf': ('PDF Document', 'application/pdf'),
            '.js': ('JavaScript', 'application/javascript'),
            '.py': ('Python Script', 'text/x-python'),
            '.ps1': ('PowerShell Script', 'application/x-powershell'),
            '.bat': ('Batch Script', 'application/x-bat'),
            '.vbs': ('VBScript', 'application/x-vbs'),
        }
        return ext_map.get(ext, ('Unknown', 'application/octet-stream'))

    except Exception:
        return 'Unknown', 'application/octet-stream'


def extract_strings(file_path: str, min_length: int = 6) -> List[str]:
    """Extract readable ASCII and Unicode strings from a binary file."""
    strings = []

    try:
        with open(file_path, 'rb') as f:
            data = f.read(5 * 1024 * 1024)  # Read first 5MB

        # ASCII strings
        ascii_pattern = re.compile(rb'[\x20-\x7e]{%d,}' % min_length)
        for match in ascii_pattern.finditer(data):
            strings.append(match.group().decode('ascii', errors='ignore'))

        # Unicode strings (UTF-16LE)
        unicode_pattern = re.compile(rb'(?:[\x20-\x7e]\x00){%d,}' % min_length)
        for match in unicode_pattern.finditer(data):
            try:
                decoded = match.group().decode('utf-16-le', errors='ignore')
                if decoded and decoded not in strings:
                    strings.append(decoded)
            except Exception:
                pass

    except Exception:
        pass

    return strings[:500]  # Cap at 500 strings


def extract_urls_and_ips(strings: List[str]) -> Tuple[List[str], List[str]]:
    """Extract URLs and IP addresses from string list."""
    url_pattern = re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+|'
        r'ftp://[^\s<>"{}|\\^`\[\]]+|'
        r'www\.[^\s<>"{}|\\^`\[\]]+'
    )

    ip_pattern = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )

    urls = set()
    ips = set()

    for s in strings:
        urls.update(url_pattern.findall(s))
        found_ips = ip_pattern.findall(s)
        # Filter common non-suspicious IPs
        for ip in found_ips:
            if ip not in ('0.0.0.0', '127.0.0.1', '255.255.255.255'):
                ips.add(ip)

    return list(urls), list(ips)


async def save_upload(upload_dir: str, file_content: bytes, original_filename: str) -> Tuple[str, str]:
    """
    Save an uploaded file with a UUID filename.
    Returns (uuid_filename, storage_path).
    """
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(original_filename)[1].lower()
    uuid_filename = f"{uuid.uuid4().hex}{ext}"
    storage_path = os.path.join(upload_dir, uuid_filename)

    async with aiofiles.open(storage_path, 'wb') as f:
        await f.write(file_content)

    return uuid_filename, storage_path


def get_file_size_display(size_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
