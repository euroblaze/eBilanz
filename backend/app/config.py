"""12-Factor Konfiguration — liest <repo>/.env. Keine Secrets im Code."""
from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo-Root: backend/app/config.py -> parents[2] = Repo-Wurzel
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000
    network_ip: str = "10.0.100.3"

    sqlite_path: str = "./data/ebilanz.sqlite"
    cors_origins: str = "http://10.0.100.3:5173,http://10.0.99.1:5173,http://localhost:5173"

    secret_key: str = "change-me"
    superadmin_email: str = "admin@euroblaze.de"
    superadmin_password: str = "change-me"

    # Vorbelegte Steuertaxonomie je Installation (eine DB pro Kunde).
    # Öffis-Instanz: "Ergänzungstaxonomie Verkehrsunternehmen (JAbschlVUV)";
    # Simplify-ERP-Instanz: "Kerntaxonomie".
    default_taxonomie_art: str = "Kerntaxonomie"

    # Unternehmens-Stammdaten-Fallback je Installation (z. B. aus dem Impressum).
    # Greift nur fuer Felder, die Odoo leer laesst. Spaeter: editierbare DB-Tabelle (todo §C).
    company_rechtsform: str = ""
    company_strasse: str = ""
    company_plz_ort: str = ""
    company_bundesland: str = ""
    company_ust_idnr: str = ""
    company_hrb: str = ""
    company_telefon: str = ""
    company_email: str = ""
    company_website: str = ""

    # Odoo (leer -> Demo-Daten)
    odoo_url: str = ""
    odoo_db: str = ""
    odoo_username: str = ""
    odoo_api_key: str = ""
    odoo_company_id: int = 1
    odoo_rpc: str = "jsonrpc"

    @cached_property
    def db_file(self) -> Path:
        p = Path(self.sqlite_path)
        return p if p.is_absolute() else (ROOT_DIR / p)

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_file}"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def odoo_configured(self) -> bool:
        return bool(self.odoo_url and self.odoo_db)


settings = Settings()
