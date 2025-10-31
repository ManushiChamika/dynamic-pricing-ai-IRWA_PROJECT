import sys
from pathlib import Path

root = Path(__file__).resolve().parent
p = str(root)
if p not in sys.path:
    sys.path.insert(0, p)
