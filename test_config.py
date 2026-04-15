from app.core.config import settings

print("ENV:", settings.app_env)
print("JWT SECRET:", settings.jwt_secret)