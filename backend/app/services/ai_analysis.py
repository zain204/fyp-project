"""
Rule-based forensic analysis engine (v1).

analyze_file() reads an evidence file, extracts features (type, entropy, URLs,
emails, IPs, keywords, ...) and produces a list of findings with a confidence
score. The interface is intentionally simple so that a machine learning model
can be plugged in later without changing the API layer.
"""

import ipaddress
import math
import re
from collections import Counter
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

ENGINE_NAME = "rule-based-v1"

MAX_READ_BYTES = 5 * 1024 * 1024  # analyze at most the first 5 MB of a file
MAX_TEXT_CHARS = 20000            # how much extracted text is stored in the database
MAX_LIST_ITEMS = 50               # cap for lists stored in the features JSON


# ======================================================================
# Data classes
# ======================================================================
def severity_from_confidence(confidence: float) -> str:
    if confidence >= 0.9:
        return "critical"
    if confidence >= 0.7:
        return "high"
    if confidence >= 0.4:
        return "medium"
    return "low"


def compute_risk(confidences: List[float]) -> Tuple[int, str]:
    """
    Combines finding confidences into one 0-100 risk score:
    risk = 1 - product(1 - confidence_i)
    """
    remaining = 1.0
    for c in confidences:
        remaining *= 1.0 - max(0.0, min(float(c), 0.99))
    score = round((1.0 - remaining) * 100)

    if score >= 80:
        level = "critical"
    elif score >= 60:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"
    return score, level


@dataclass
class FindingData:
    finding_type: str
    title: str
    description: str
    confidence: float

    @property
    def severity(self) -> str:
        return severity_from_confidence(self.confidence)


@dataclass
class AnalysisOutput:
    features: Dict[str, Any]
    extracted_text: str
    findings: List[FindingData]


# ======================================================================
# Constants
# ======================================================================
MAGIC_SIGNATURES: List[Tuple[bytes, str]] = [
    (b"\x7fELF", "linux_executable"),
    (b"%PDF", "pdf"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"PK\x03\x04", "zip"),
    (b"Rar!", "rar"),
    (b"7z\xbc\xaf\x27\x1c", "7z"),
    (b"\x1f\x8b", "gzip"),
    (b"SQLite format 3\x00", "sqlite"),
    (b"\xd0\xcf\x11\xe0", "ole_office"),
]

EXT_EXPECTED: Dict[str, set] = {
    ".pdf": {"pdf"},
    ".png": {"png"},
    ".jpg": {"jpeg"},
    ".jpeg": {"jpeg"},
    ".gif": {"gif"},
    ".zip": {"zip"},
    ".docx": {"zip"},
    ".xlsx": {"zip"},
    ".pptx": {"zip"},
    ".jar": {"zip"},
    ".apk": {"zip"},
    ".rar": {"rar"},
    ".7z": {"7z"},
    ".gz": {"gzip"},
    ".db": {"sqlite"},
    ".sqlite": {"sqlite"},
    ".doc": {"ole_office"},
    ".xls": {"ole_office"},
    ".exe": {"windows_executable"},
    ".dll": {"windows_executable"},
}

EXECUTABLE_EXTS = {".exe", ".dll", ".scr", ".com", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".sh"}
SCRIPT_EXTS = {".bat", ".cmd", ".ps1", ".vbs", ".js", ".sh"}
DANGEROUS_ATTACHMENT_EXTS = {
    ".exe", ".dll", ".scr", ".com", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jar", ".apk", ".iso", ".lnk",
}
HIGH_ENTROPY_NORMAL_TYPES = {"zip", "rar", "7z", "gzip", "png", "jpeg", "gif", "pdf", "ole_office"}

PHISHING_KEYWORDS: Dict[str, List[str]] = {
    "urgency": [
        "urgent", "immediately", "within 24 hours", "act now", "final notice",
        "account suspended", "your account will be", "limited time", "expires today",
        "verify immediately",
    ],
    "credentials": [
        "verify your account", "confirm your password", "update your password",
        "login to your account", "log in to your account", "security alert",
        "unusual activity", "sign in to confirm", "reset your password",
        "enter your otp", "one time password",
    ],
    "financial": [
        "wire transfer", "bank account", "credit card", "western union", "gift card",
        "bitcoin", "crypto wallet", "payment failed", "invoice attached", "refund",
        "lottery", "you have won", "prize", "inheritance",
    ],
}

MALWARE_INDICATORS: List[str] = [
    "virtualalloc", "writeprocessmemory", "createremotethread", "urldownloadtofile",
    "winexec", "shellexecute", "keylogger", "mimikatz", "powershell -enc",
    "powershell -e ", "frombase64string", "invoke-expression", "iex(", "wscript.shell",
    "cmd.exe /c", "schtasks /create", "reg add", "eval(unescape", "document.write(unescape",
]

RANSOM_PHRASES: List[str] = [
    "your files have been encrypted", "decrypt your files", "pay the ransom",
    "all your files are encrypted", "send bitcoin to recover",
]

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly", "buff.ly",
    "rebrand.ly", "cutt.ly", "shorturl.at", "tiny.cc",
}
RISKY_TLDS = {"tk", "ml", "ga", "cf", "gq", "xyz", "top", "click", "zip", "mov", "icu", "buzz"}
BRAND_DOMAINS = {
    "paypal": "paypal.com",
    "facebook": "facebook.com",
    "google": "google.com",
    "microsoft": "microsoft.com",
    "apple": "apple.com",
    "amazon": "amazon.com",
    "netflix": "netflix.com",
    "instagram": "instagram.com",
    "whatsapp": "whatsapp.com",
    "binance": "binance.com",
    "easypaisa": "easypaisa.com.pk",
    "jazzcash": "jazzcash.com.pk",
}

URL_RE = re.compile(r"https?://[^\s<>\"'\)\]]+", re.IGNORECASE)
IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
BTC_RE = re.compile(r"\b(?:bc1[a-z0-9]{25,59}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")
CARD_RE = re.compile(r"\b(?:\d[ \-]?){13,19}\b")
PASSWORD_RE = re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*\S+", re.IGNORECASE)


# ======================================================================
# Low-level helpers
# ======================================================================
def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _is_pe(data: bytes) -> bool:
    """Checks for a real Windows PE header (so a text file starting with 'MZ' is not flagged)."""
    if len(data) < 0x40 or not data.startswith(b"MZ"):
        return False
    offset = int.from_bytes(data[0x3C:0x40], "little")
    return 0 < offset < len(data) - 4 and data[offset:offset + 4] == b"PE\x00\x00"


def looks_like_text(sample: bytes) -> bool:
    if not sample:
        return False
    if b"\x00" in sample:
        return False
    control = sum(1 for b in sample if b < 32 and b not in (9, 10, 13))
    return control / len(sample) < 0.05


def detect_type(data: bytes, is_text: bool) -> str:
    if _is_pe(data):
        return "windows_executable"
    for signature, name in MAGIC_SIGNATURES:
        if data.startswith(signature):
            return name
    if data.startswith(b"#!"):
        return "script"
    return "text" if is_text else "unknown"


def _extract_strings(data: bytes, limit: int = 500_000) -> str:
    """Printable ASCII strings from a binary file (like the Unix 'strings' tool)."""
    parts: List[str] = []
    total = 0
    for match in re.finditer(rb"[\x20-\x7e]{6,}", data):
        piece = match.group().decode("ascii")
        parts.append(piece)
        total += len(piece) + 1
        if total >= limit:
            break
    return "\n".join(parts)


def _luhn_ok(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        digit = int(ch)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _unique(items: List[str], limit: int = MAX_LIST_ITEMS) -> List[str]:
    seen: Dict[str, None] = {}
    for item in items:
        seen.setdefault(item, None)
        if len(seen) >= limit:
            break
    return list(seen.keys())


def _domain_of(address: str) -> str:
    return address.split("@")[-1].lower().strip() if "@" in address else ""


# ======================================================================
# URL analysis
# ======================================================================
def analyze_url(url: str) -> List[str]:
    """Returns a list of human readable reasons why a URL looks suspicious."""
    reasons: List[str] = []
    try:
        parsed = urlparse(url)
    except ValueError:
        return ["is malformed"]

    host = (parsed.hostname or "").lower()
    if not host:
        return reasons

    try:
        ipaddress.ip_address(host)
        reasons.append("uses a raw IP address instead of a domain name")
    except ValueError:
        pass

    if host in URL_SHORTENERS:
        reasons.append("uses a URL shortening service")
    if "xn--" in host:
        reasons.append("contains punycode (possible look-alike characters)")
    if "@" in parsed.netloc:
        reasons.append("contains an embedded '@' (credential trick)")

    tld = host.rsplit(".", 1)[-1]
    if tld in RISKY_TLDS:
        reasons.append(f"uses a high-risk top-level domain (.{tld})")
    if host.count(".") >= 4:
        reasons.append("has an unusually deep subdomain chain")

    tokens = re.split(r"[.\-_]", host)
    for brand, legit in BRAND_DOMAINS.items():
        if brand in tokens and not (host == legit or host.endswith("." + legit)):
            reasons.append(f"impersonates the brand '{brand}'")
            break

    return reasons


# ======================================================================
# Email analysis
# ======================================================================
def _parse_email(data: bytes) -> Optional[Dict[str, Any]]:
    try:
        msg = BytesParser(policy=policy.default).parsebytes(data)
    except Exception:
        return None

    def header(name: str) -> str:
        value = msg.get(name)
        return str(value) if value else ""

    from_addr = parseaddr(header("From"))[1].lower()
    reply_to = parseaddr(header("Reply-To"))[1].lower()
    return_path = parseaddr(header("Return-Path"))[1].lower()
    subject = header("Subject")

    body_text = ""
    hrefs: List[str] = []
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
        if part is not None:
            content = part.get_content()
            if part.get_content_type() == "text/html":
                hrefs = re.findall(r"href=[\"']([^\"']+)", content, re.IGNORECASE)
                body_text = re.sub(r"<[^>]+>", " ", content)
            else:
                body_text = content
    except Exception:
        body_text = ""

    attachments: List[str] = []
    try:
        for attachment in msg.iter_attachments():
            name = attachment.get_filename()
            if name:
                attachments.append(name)
    except Exception:
        pass

    auth_text = (header("Authentication-Results") + " " + header("Received-SPF")).lower()
    auth_failures = [
        marker for marker in ("spf=fail", "spf=softfail", "dkim=fail", "dmarc=fail")
        if marker in auth_text
    ]

    received = msg.get_all("Received") or []

    text = "\n".join([subject, body_text, " ".join(hrefs)])

    return {
        "text": text,
        "info": {
            "from": from_addr,
            "reply_to": reply_to,
            "return_path": return_path,
            "subject": subject,
            "received_hops": len(received),
            "attachments": attachments[:MAX_LIST_ITEMS],
            "auth_failures": auth_failures,
        },
    }


def _email_findings(info: Dict[str, Any]) -> List[FindingData]:
    findings: List[FindingData] = []

    from_domain = _domain_of(info["from"])
    reply_domain = _domain_of(info["reply_to"])
    return_domain = _domain_of(info["return_path"])

    if from_domain and reply_domain and from_domain != reply_domain:
        findings.append(FindingData(
            "email_spoofing",
            "Reply-To domain differs from sender domain",
            f"The email claims to be from '{from_domain}' but replies are directed to "
            f"'{reply_domain}'. This is a common phishing and impersonation technique.",
            0.60,
        ))

    if from_domain and return_domain and from_domain != return_domain:
        findings.append(FindingData(
            "email_spoofing",
            "Return-Path domain differs from sender domain",
            f"The sender domain is '{from_domain}' but the return path is '{return_domain}'. "
            "This can indicate a spoofed sender (it can also be a legitimate mailing service).",
            0.40,
        ))

    if info["auth_failures"]:
        findings.append(FindingData(
            "email_authentication_failure",
            "Email authentication checks failed",
            "The message headers report failed sender authentication: "
            + ", ".join(info["auth_failures"])
            + ". The sender may be forged.",
            0.80,
        ))

    dangerous = [
        name for name in info["attachments"]
        if Path(name).suffix.lower() in DANGEROUS_ATTACHMENT_EXTS
    ]
    if dangerous:
        findings.append(FindingData(
            "malicious_attachment",
            "Email contains a potentially dangerous attachment",
            "Attachment(s) with executable or script file types: " + ", ".join(dangerous[:5]) + ".",
            0.85,
        ))

    return findings


# ======================================================================
# Main entry point
# ======================================================================
def analyze_file(path: Path, original_filename: str) -> AnalysisOutput:
    size = path.stat().st_size
    with open(path, "rb") as f:
        data = f.read(MAX_READ_BYTES)

    ext = Path(original_filename).suffix.lower()
    is_text = looks_like_text(data[:8192])
    detected = detect_type(data, is_text)
    entropy = round(shannon_entropy(data), 3)

    findings: List[FindingData] = []
    features: Dict[str, Any] = {
        "analysis_engine": ENGINE_NAME,
        "file_name": original_filename,
        "extension": ext,
        "size_bytes": size,
        "analyzed_bytes": len(data),
        "truncated": size > len(data),
        "detected_type": detected,
        "is_text": is_text,
        "entropy": entropy,
    }

    # ---------------- Text extraction ----------------
    if is_text:
        text = data.decode("utf-8", errors="replace")
    else:
        text = _extract_strings(data)

    # ---------------- Email handling ----------------
    head = text[:4000].lower()
    header_hits = sum(h in head for h in ("from:", "subject:", "received:", "message-id:", "to:"))
    if ext == ".eml" or (is_text and header_hits >= 4):
        parsed_email = _parse_email(data)
        if parsed_email is not None:
            text = parsed_email["text"]
            features["email"] = parsed_email["info"]
            findings.extend(_email_findings(parsed_email["info"]))

    lowered = text.lower()

    # ---------------- File type findings ----------------
    if detected in ("windows_executable", "linux_executable"):
        if ext not in EXECUTABLE_EXTS:
            findings.append(FindingData(
                "disguised_executable",
                "Executable disguised as another file type",
                f"The file is named '{original_filename}' but its content is an executable "
                f"program ({detected.replace('_', ' ')}). Attackers rename executables to trick users.",
                0.92,
            ))
        else:
            findings.append(FindingData(
                "executable_file",
                "Executable file",
                "The evidence is an executable program. It should be analyzed only in an isolated environment.",
                0.60,
            ))
    elif ext in EXT_EXPECTED and detected not in EXT_EXPECTED[ext]:
        findings.append(FindingData(
            "extension_mismatch",
            "File extension does not match file content",
            f"The extension '{ext}' suggests a different format than the detected content "
            f"type '{detected}'. The file may have been renamed or disguised.",
            0.70,
        ))

    if ext in SCRIPT_EXTS or detected == "script":
        findings.append(FindingData(
            "script_file",
            "Script file",
            "The evidence is a script. Scripts can execute commands and are often used to deliver malware.",
            0.45,
        ))

    if len(data) >= 4096 and entropy > 7.5 and detected not in HIGH_ENTROPY_NORMAL_TYPES:
        confidence = 0.65 if detected in ("windows_executable", "linux_executable") else 0.55
        findings.append(FindingData(
            "high_entropy",
            "Possible encrypted or packed content",
            f"The file has very high entropy ({entropy} out of 8.0), which usually means "
            "encrypted, compressed or packed data that hides its real content.",
            confidence,
        ))

    # ---------------- Indicators extraction ----------------
    urls = _unique([u.rstrip(".,;:!?)>]}'\"") for u in URL_RE.findall(text)])
    ips = _unique([ip for ip in IPV4_RE.findall(text) if _valid_ip(ip)])
    emails = _unique([e.lower() for e in EMAIL_RE.findall(text)])
    wallets = _unique(BTC_RE.findall(text), limit=10)

    suspicious_urls: List[Dict[str, Any]] = []
    for url in urls:
        reasons = analyze_url(url)
        if reasons:
            suspicious_urls.append({"url": url[:200], "reasons": reasons})

    keyword_hits: Dict[str, List[str]] = {
        category: [p for p in phrases if p in lowered]
        for category, phrases in PHISHING_KEYWORDS.items()
    }

    features.update({
        "url_count": len(urls),
        "urls": urls,
        "ip_addresses": ips,
        "email_addresses": emails,
        "crypto_wallets": wallets,
        "suspicious_urls": suspicious_urls[:20],
        "keyword_hits": {k: v for k, v in keyword_hits.items() if v},
    })

    # ---------------- Suspicious URLs ----------------
    if suspicious_urls:
        confidence = min(0.90, 0.45 + 0.10 * len(suspicious_urls))
        sample = "; ".join(
            f"{item['url']} ({item['reasons'][0]})" for item in suspicious_urls[:3]
        )
        findings.append(FindingData(
            "suspicious_url",
            f"{len(suspicious_urls)} suspicious URL(s) found",
            f"Examples: {sample}",
            confidence,
        ))

    # ---------------- Phishing score ----------------
    urgency = len(keyword_hits["urgency"])
    credentials = len(keyword_hits["credentials"])
    financial = len(keyword_hits["financial"])

    phishing_score = (
        min(2, urgency) * 0.12
        + min(3, credentials) * 0.15
        + min(2, financial) * 0.08
        + min(3, len(suspicious_urls)) * 0.15
    )
    if urls and credentials:
        phishing_score += 0.10
    phishing_score = min(phishing_score, 0.97)

    if phishing_score >= 0.35:
        findings.append(FindingData(
            "phishing",
            "Phishing indicators detected",
            f"The content matches common phishing patterns: urgency phrases ({urgency}), "
            f"credential requests ({credentials}), financial lures ({financial}) and "
            f"{len(suspicious_urls)} suspicious URL(s).",
            round(phishing_score, 2),
        ))

    # ---------------- Malware / ransomware ----------------
    malware_hits = [m for m in MALWARE_INDICATORS if m in lowered]
    if malware_hits:
        features["malware_indicators"] = malware_hits[:MAX_LIST_ITEMS]
    if len(malware_hits) >= 2:
        findings.append(FindingData(
            "malware_indicators",
            "Malware-related strings found",
            f"{len(malware_hits)} suspicious command or API names were found, for example: "
            + ", ".join(malware_hits[:5]) + ".",
            round(min(0.95, 0.35 + 0.12 * len(malware_hits)), 2),
        ))

    ransom_hits = [p for p in RANSOM_PHRASES if p in lowered]
    if ransom_hits:
        findings.append(FindingData(
            "ransomware_note",
            "Possible ransomware note",
            "The content contains phrases typical of a ransom demand: "
            + ", ".join(ransom_hits[:3]) + ".",
            0.85,
        ))

    # ---------------- Sensitive data ----------------
    card_count = 0
    for match in CARD_RE.findall(text):
        digits = re.sub(r"\D", "", match)
        if 13 <= len(digits) <= 19 and len(set(digits)) > 2 and _luhn_ok(digits):
            card_count += 1
    if card_count:
        features["possible_card_numbers"] = card_count
        findings.append(FindingData(
            "sensitive_data",
            "Possible payment card numbers found",
            f"{card_count} value(s) that look like payment card numbers (valid Luhn checksum) "
            "were found. The values are not displayed for privacy reasons.",
            0.70,
        ))

    password_count = len(PASSWORD_RE.findall(text))
    if password_count:
        features["password_patterns"] = password_count
        findings.append(FindingData(
            "credential_exposure",
            "Possible exposed credentials",
            f"{password_count} 'password: value' style pattern(s) were found. "
            "The values are not displayed for privacy reasons.",
            0.65,
        ))

    # ---------------- Crypto wallets ----------------
    if wallets:
        findings.append(FindingData(
            "crypto_wallet",
            f"{len(wallets)} cryptocurrency wallet address(es) found",
            "Wallet addresses can help trace payments in fraud and ransomware cases: "
            + ", ".join(wallets[:5]) + ".",
            0.55,
        ))

    findings.sort(key=lambda f: f.confidence, reverse=True)

    return AnalysisOutput(
        features=features,
        extracted_text=text[:MAX_TEXT_CHARS],
        findings=findings,
    )


def _valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False