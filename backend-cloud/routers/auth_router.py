from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import uuid

import models
import schemas
import auth
from database import get_db
from logger import logger

router = APIRouter(tags=["Authentication"])

@router.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logger.info(f"Successful login for {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/api/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

@router.get("/api/setup/status")
def setup_status(db: Session = Depends(get_db)):
    """Check if the system requires the first-run wizard."""
    admin = db.query(models.User).filter_by(role="admin").first()
    return {"requires_setup": admin is None}

@router.post("/api/setup/initialize")
def setup_initialize(payload: schemas.SetupInitialize, db: Session = Depends(get_db)):
    """One-time setup to create admin user and initial API Key via Wizard."""
    admin = db.query(models.User).filter_by(role="admin").first()
    if admin:
        raise HTTPException(status_code=400, detail="System already configured")
    
    hashed_pw = auth.get_password_hash(payload.password)
    user = models.User(id=str(uuid.uuid4()), email=payload.email, hashed_password=hashed_pw, role="admin")
    db.add(user)
    
    api_key_str = "agent-" + str(uuid.uuid4())
    api_key = models.APIKey(id=str(uuid.uuid4()), key=api_key_str, name="Primary Local Agent Key")
    db.add(api_key)
    
    db.commit()
    logger.info(f"System successfully initialized via Wizard by {payload.email}")
    return {
        "msg": "Setup complete",
        "api_key": api_key_str,
        "company_name": payload.company_name
    }

@router.post("/api/register")
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(models.User).filter_by(email=user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.get_password_hash(user_data.password)
    user = models.User(
        id=str(uuid.uuid4()), 
        email=user_data.email, 
        hashed_password=hashed_pw
    )
    db.add(user)
    db.commit()
    return {"msg": "User created successfully"}

@router.get("/api/keys")
def list_api_keys(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """List API keys for the authenticated user to configure their local agent."""
    keys = db.query(models.APIKey).all()
    return [{"name": k.name, "key": k.key, "is_active": k.is_active} for k in keys]
