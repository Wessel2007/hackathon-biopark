from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    dashboard_email: str
    dashboard_password: str

    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    openai_api_key: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
