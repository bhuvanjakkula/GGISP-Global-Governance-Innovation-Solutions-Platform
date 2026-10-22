import base64
from pathlib import Path

index_bytes = Path("index.html").read_bytes()
pricing_bytes = Path("pricing.html").read_bytes()

index_b64 = base64.b64encode(index_bytes).decode("ascii")
pricing_b64 = base64.b64encode(pricing_bytes).decode("ascii")

code = f'''"""Embedded HTML pages for zero-filesystem serverless execution."""
import base64

_INDEX_B64 = "{index_b64}"
_PRICING_B64 = "{pricing_b64}"

INDEX_BYTES: bytes = base64.b64decode(_INDEX_B64)
PRICING_BYTES: bytes = base64.b64decode(_PRICING_B64)

INDEX_HTML: str = INDEX_BYTES.decode("utf-8")
PRICING_HTML: str = PRICING_BYTES.decode("utf-8")
'''

Path("ggisp/embedded_pages.py").write_text(code, encoding="utf-8")
print("ggisp/embedded_pages.py regenerated cleanly via Base64!")
