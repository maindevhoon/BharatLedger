"""
Central configuration for the Bharat Ledger offline pipeline (and shared by api/).

Design rule (see PLAN.md §5, cross-cutting requirement #3): every flag here defaults to the
*safe, fully-offline* value. The app must run end-to-end with no network and no GCP credentials
using these defaults. Flip flags on only once the corresponding cloud setup is verified.

Reads from a `.env` file at the repo root if present (via python-dotenv), falling back to
process environment variables, falling back to the hardcoded defaults below.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    _REPO_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(_REPO_ROOT / ".env", override=False)
except ImportError:
    # python-dotenv not installed yet — fine, we just rely on real env vars / defaults.
    _REPO_ROOT = Path(__file__).resolve().parent.parent


def _bool_env(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _str_env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Config:
    # ---- repo paths ----
    repo_root: Path = field(default_factory=lambda: _REPO_ROOT)

    # ---- Google Cloud ----
    gcp_project: str = field(default_factory=lambda: _str_env("GOOGLE_CLOUD_PROJECT", "personal-hackthon-tests"))
    gcp_location: str = field(default_factory=lambda: _str_env("GOOGLE_CLOUD_LOCATION", "asia-south1"))

    # ---- feature flags (default = fully offline / mocked) ----
    use_bigquery: bool = field(default_factory=lambda: _bool_env("USE_BIGQUERY", False))
    use_vertex_ai: bool = field(default_factory=lambda: _bool_env("USE_VERTEX_AI", False))
    use_document_ai: bool = field(default_factory=lambda: _bool_env("USE_DOCUMENT_AI", False))
    enable_live_debate_endpoint: bool = field(
        default_factory=lambda: _bool_env("ENABLE_LIVE_DEBATE_ENDPOINT", True)
    )

    # ---- models ----
    gemini_flash_model: str = field(default_factory=lambda: _str_env("GEMINI_FLASH_MODEL", "gemini-2.5-flash"))
    gemini_pro_model: str = field(default_factory=lambda: _str_env("GEMINI_PRO_MODEL", "gemini-2.5-pro"))

    # ---- document ai ----
    document_ai_processor_id: str = field(default_factory=lambda: _str_env("DOCUMENT_AI_PROCESSOR_ID", ""))

    # ---- data paths ----
    sqlite_path: Path = field(
        default_factory=lambda: _REPO_ROOT / _str_env("SQLITE_PATH", "data/bharat_ledger.sqlite")
    )
    raw_pdf_dir: Path = field(default_factory=lambda: _REPO_ROOT / _str_env("RAW_PDF_DIR", "data/raw_pdfs"))
    synthetic_dir: Path = field(default_factory=lambda: _REPO_ROOT / _str_env("SYNTHETIC_DIR", "data/synthetic"))
    seed_dir: Path = field(default_factory=lambda: _REPO_ROOT / _str_env("SEED_DIR", "data/seed"))

    # ---- API ----
    api_host: str = field(default_factory=lambda: _str_env("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(_str_env("API_PORT", "8000")))
    cors_origins: tuple = field(
        default_factory=lambda: tuple(
            o.strip() for o in _str_env("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
        )
    )

    # ---- responsible-AI language guard (PLAN.md §5.1 / ARCHITECTURE.md §9) ----
    banned_terms: tuple = field(
        default_factory=lambda: (
            "corrupt", "corruption", "scam", "loot", "looted", "fraud", "fraudulent",
            "stolen", "embezzle", "embezzled", "embezzlement", "bribe", "bribery",
            "criminal", "crony", "swindle", "graft",
        )
    )

    def __post_init__(self) -> None:
        # Ensure data directories exist so first-run scripts don't fail on missing folders.
        # Skip entirely if a directory already exists (the case on every read-only deployment
        # filesystem, e.g. Vercel — attempting mkdir there raises OSError/EROFS even with
        # exist_ok=True, since the read-only check happens before the exists check).
        for d in (self.raw_pdf_dir, self.synthetic_dir, self.seed_dir, self.sqlite_path.parent):
            if d.exists():
                continue
            try:
                d.mkdir(parents=True, exist_ok=True)
            except OSError:
                # Read-only filesystem and the directory doesn't exist — nothing we can do at
                # import time; let downstream code fail with a clearer error if it actually
                # needs to write there.
                pass


config = Config()


def contains_banned_language(text: str) -> list[str]:
    """Return the list of banned terms (see agent.md §3) found in `text`, case-insensitive.

    Used as a correctness gate in batch_score.py: any hit means generated rationale/arguments
    violated the responsible-AI framing and must not be cached as-is.
    """
    if not text:
        return []
    lowered = text.lower()
    return [term for term in config.banned_terms if term in lowered]


if __name__ == "__main__":
    # Quick manual sanity check: `python -m pipeline.config`
    import json

    print(json.dumps({
        "repo_root": str(config.repo_root),
        "gcp_project": config.gcp_project,
        "gcp_location": config.gcp_location,
        "use_bigquery": config.use_bigquery,
        "use_vertex_ai": config.use_vertex_ai,
        "use_document_ai": config.use_document_ai,
        "sqlite_path": str(config.sqlite_path),
    }, indent=2))
