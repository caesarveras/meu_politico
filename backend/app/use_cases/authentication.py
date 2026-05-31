from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OAuthRequest(BaseModel):
    token: str


class AuthenticationUseCase:
    def login_with_password(self, payload: LoginRequest):
        return {
            "access_token": "dev-token",
            "token_type": "bearer",
            "user": {
                "email": payload.email,
                "provider": "password",
                "permissions": ["favorites:write", "follows:write"],
            },
        }

    def login_with_google(self, payload: OAuthRequest):
        return {"provider": "google", "status": "configured", "token_preview": payload.token[:10]}

    def login_with_microsoft(self, payload: OAuthRequest):
        return {"provider": "microsoft", "status": "configured", "token_preview": payload.token[:10]}

    def get_current_user(self):
        return {
            "name": "Usuário Demo",
            "email": "demo@meuspoliticos.com.br",
            "locale": "pt-BR",
            "providers": ["password", "google", "microsoft"],
        }


authentication_use_case = AuthenticationUseCase()
