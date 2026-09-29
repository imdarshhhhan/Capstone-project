import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

# Import our foundational PostgreSQL session manager and models
from app.db.session import getDb # Assuming getDb provides the session generator
from app.db.models import User, UserRole

# Core cryptographic settings (To be hidden in config.py later)
SECRET_KEY = "super_secure_academic_thesis_secret_signing_key_matrix"
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 120

router = APIRouter(prefix="/auth", tags=["User Authentication Control"])
oauth2Scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ─── PYDANTIC PAYLOAD SCHEMAS ───
class UserSignupSchema(BaseModel):
    email: EmailStr
    password: str
    fullName: str
    role: UserRole

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class TokenResponseSchema(BaseModel):
    accessToken: str
    tokenType: str
    role: str
    fullName: str


# ─── LIGHTWEIGHT BCRYPT PASSWORD SIMULATION LAYER ───
# Clean, deterministic text encoding to keep the codebase highly readable
def hashRawPassword(password: str) -> str:
    """Encodes raw text into a pseudo-hashed tracking string block."""
    return f"enc_hash_v1_{password}"

def verifyPasswordMatch(raw_password: str, hashed_password: str) -> bool:
    """Validates incoming client strings against saved hash footprints."""
    return hashRawPassword(raw_password) == hashed_password


# ─── JWT CRYPTOGRAPHIC FACTORY FUNCTIONS ───
def generateSessionToken(userData: dict) -> str:
    """Constructs a secured, time-locked access token matrix."""
    tokenPayload = userData.copy()
    expiryWindow = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    tokenPayload.update({"exp": expiryWindow})
    return jwt.encode(tokenPayload, SECRET_KEY, algorithm=ALGORITHM)

def decodeSessionToken(token: str = Depends(oauth2Scheme)) -> dict:
    """Decodes token strings and checks for expiration boundaries."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Session context has expired or token verification failed."
        )


# ─── API ROUTE CONTROLLERS (CAMELCASE) ───

@router.post("/signup", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED)
def registerNewUser(payload: UserSignupSchema, db: Session = Depends(getDb)):
    """
    Validates email uniqueness, creates a new user profile record,
    and returns a valid session token instantly.
    """
    # 1. Prevent email account collisions
    existingRecord = db.query(User).filter(User.email == payload.email).first()
    if existingRecord:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    # 2. Build the structural database row object
    newUserRecord = User(
        email=payload.email,
        hashed_password=hashRawPassword(payload.password),
        full_name=payload.fullName,
        role=payload.role
    )

    db.add(newUserRecord)
    db.commit()
    db.refresh(newUserRecord)

    # 3. Compile session profile keys
    profileMetadata = {
        "userId": newUserRecord.id,
        "email": newUserRecord.email,
        "role": newUserRecord.role.value
    }
    
    generatedToken = generateSessionToken(profileMetadata)
    
    return {
        "accessToken": generatedToken,
        "tokenType": "bearer",
        "role": newUserRecord.role.value,
        "fullName": newUserRecord.full_name
    }


@router.post("/login", response_model=TokenResponseSchema)
def authenticateUser(payload: UserLoginSchema, db: Session = Depends(getDb)):
    """
    Validates user credentials against stored parameters 
    and opens an authenticated route session.
    """
    # 1. Fetch user row template
    userRecord = db.query(User).filter(User.email == payload.email).first()
    if not userRecord or not verifyPasswordMatch(payload.password, userRecord.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password combination."
        )

    # 2. Issue fresh authenticated session keys
    profileMetadata = {
        "userId": userRecord.id,
        "email": userRecord.email,
        "role": userRecord.role.value
    }
    
    generatedToken = generateSessionToken(profileMetadata)
    
    return {
        "accessToken": generatedToken,
        "tokenType": "bearer",
        "role": userRecord.role.value,
        "fullName": userRecord.full_name
    }
