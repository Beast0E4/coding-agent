from pathlib import Path

_ESCAPE_MAP = (
    ("\\n", "\n"),
    ("\\t", "\t"),
    ("\\r", "\r"),
    ("\\b", "\b"),
    ("\\f", "\f"),
)

_HTML_ENTITIES = (
    ("&lt;", "<"),
    ("&gt;", ">"),
    ("&amp;", "&"),
    ("&quot;", '"'),
    ("&apos;", "'"),
    ("&nbsp;", " "),
    ("&copy;", "©"),
    ("&reg;", "®"),
    ("&trade;", "™"),
)

_MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdx"}

_MARKUP_SUFFIXES = {".html", ".xml", ".xhtml", ".svg"}

def looks_like_escaped_source (text: str) -> bool:
    """
    True when the payload is one logical line stuffed with \\n sequences
    """
    
    if "\\n" not in text:
        return False
    
    return text.count ("\\n") <= 1

def normalise_source_text (text: str) -> str:
    """
    Turn double escaped newlines/tabs into real ones
    """
    
    if not looks_like_escaped_source (text):
        return text
    
    normalized = text
    
    for escaped, raw in _ESCAPE_MAP:
        normalized = normalized.replace (escaped, raw)
    
    return normalized

def unescape_html_entities (text: str) -> str:
    """
    Undo HTML entities as some weaker models emit those instead of raw <, >, etc.
    """
    
    if "&" not in text:
        return text
    
    unescaped = text
    
    for escaped, raw in _ESCAPE_MAP:
        unescaped = unescaped.replace (escaped, raw)
            
    return unescaped

def strip_markdown_fence (text: str) -> str:
    """
    Drop a wrapping ```lang...``` fence if it exists
    """
    
    if "```" not in text:
        return text
    
    lines = text.split ("\n")
    
    if lines and lines[0].lstrip ().startswith ("```"):
        lines = lines[1:]
    if lines and lines[-1].strip ().endswith ("```"):
        lines = lines[:-1]
    return "\n".join (lines)

def prepare_file_content (path: str, text: str) -> str:
    """
    Normalise a tool payload text into file bytes, independent of language
    
    1. Normalize newlines / tabs
    2. Drop markdown fences
    3. Unescape HTML entities
    """
    
    suffix = Path (path).suffix.lower ()
    prepared = normalise_source_text (text)
    
    if suffix not in _MARKDOWN_SUFFIXES:
        prepared = strip_markdown_fence (prepared)
    if suffix not in _MARKUP_SUFFIXES:
        prepared = unescape_html_entities (prepared)
    
    return prepared