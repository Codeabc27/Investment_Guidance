from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.services.auth_service import register_user, authenticate_user, create_access_token
from app.services.security import bearer, get_current_user, revoke_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(request: RegisterRequest):
    try:
        user = register_user(request.email, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AuthResponse(
        access_token=create_access_token(user["id"]),
        user_id=user["id"],
        email=user["email"],
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return AuthResponse(
        access_token=create_access_token(user["id"]),
        user_id=user["id"],
        email=user["email"],
    )


@router.post("/logout", status_code=204, dependencies=[Depends(get_current_user)])
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> None:
    revoke_access_token(credentials.credentials)
