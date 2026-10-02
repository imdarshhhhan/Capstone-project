from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer
from  db.sessions import getDb

# ─── CORRECT LAYOUT: PULL FIREBASE DIRECTLY FROM ITS OFFICIAL LIBRARY ───
import firebase_admin
from firebase_admin import credentials, auth as firebaseAuth

# Pull only the hidden environment variables from your app config settings
from  config import settings


from fastapi.security import OAuth2PasswordBearer


router = APIRouter(prefix="/auth", tags=["Federated User Authentication Control"])

# ─── ADD THIS EXACT DEFINITION LINE RIGHT HERE ───
oauth2Scheme = OAuth2PasswordBearer(tokenUrl="auth/verify-sync-login")

# Now your dependency function runs perfectly right below it:
def verifyFirebaseTokenDependency(token: str = Depends(oauth2Scheme), db: Session = Depends(getDb)) -> dict:
    """
    [HYBRID SECURE IDENTITY GATEWAY]:
    Intercepts incoming HTTP headers, decrypts the token against Firebase's public keys,
    cross-references the uid with our local PostgreSQL database rows, and returns a verified user profile object.
    """
    try:
        decodedToken = firebaseAuth.verify_id_token(token)
        firebaseUid = decodedToken["uid"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f"Session has expired or authentication validation failed: {str(e)}"
        )
