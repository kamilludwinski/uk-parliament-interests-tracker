from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "store.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"
