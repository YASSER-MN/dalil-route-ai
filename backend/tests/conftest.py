from __future__ import annotations

import sys
from pathlib import Path

# Make `from app.` imports resolve when pytest runs from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")
