from fastapi import APIRouter

from app.use_cases.authentication import LoginRequest, OAuthRequest, authentication_use_case

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest):
    return authentication_use_case.login_with_password(payload)


@router.post("/oauth/google")
def login_google(payload: OAuthRequest):
    return authentication_use_case.login_with_google(payload)


@router.post("/oauth/microsoft")
def login_microsoft(payload: OAuthRequest):
    return authentication_use_case.login_with_microsoft(payload)


@router.get("/me")
def me():
    return authentication_use_case.get_current_user()
