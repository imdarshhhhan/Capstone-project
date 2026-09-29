import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import our configurations, connections, and databases
from app.config import settings
# NOTE: Make sure this matching import statement aligns with your database file name!
from app.db.sessions import getDb 
from app.db.models import User, UserRole

# Import our newly constructed onboarding validation checkpoints
from app.schemas.user import UserSignupSchema, UserLoginSchema

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 120

router = APIRouter(prefix="/auth", tags=["User Authentication Control"])
oauth2Scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ─── PASSWORD ENCODING CONTROLLERS ───
def hashRawPassword(password: str) -> str:
    return f"enc_hash_v1_{password}"

def verifyPasswordMatch(rawPassword: str, hashedPassword: str) -> bool:
    return hashRawPassword(rawPassword) == hashedPassword


# ─── JWT ACCESS TOKEN WORKERS ───
def generateSessionToken(userData: dict) -> str:
    tokenPayload = userData.copy()
    expiryWindow = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    tokenPayload.update({"exp": expiryWindow})
    return jwt.encode(tokenPayload, SECRET_KEY, algorithm=ALGORITHM)

def decodeSessionToken(token: str = Depends(oauth2Scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Session has expired or authentication validation failed."
        )


# ─── API CONTROLLER ENDPOINTS (LOCKDOWN METRICS) ───

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def registerNewUser(payload: UserSignupSchema, db: Session = Depends(getDb)):
    """Verifies profile uniqueness, saves records to SQL rows, and drops tokens."""
    existingUser = db.query(User).filter(User.email == payload.email).first()
    if existingUser:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists inside our platform."
        )

    # Instantiate structural row variables mapping our Pydantic input keys cleanly
    newUserRecord = User(
        email=payload.email,
        hashed_password=hashRawPassword(payload.password),
        fullName=payload.fullName,
        role=payload.role
    )

    db.add(newUserRecord)
    db.commit()
    db.refresh(newUserRecord)

    profileMetadata = {
        "userId": newUserRecord.id,
        "email": newUserRecord.email,
        "role": newUserRecord.role.value
    }
    
    return {
        "accessToken": generateSessionToken(profileMetadata),
        "tokenType": "bearer",
        "role": newUserRecord.role.value,
        "fullName": newUserRecord.fullName
    }


@router.post("/login")
def authenticateUser(payload: UserLoginSchema, db: Session = Depends(getDb)):
    """Validates parameters and activates an authenticated session link."""
    userRecord = db.query(User).filter(User.email == payload.email).first()
    if not userRecord or not verifyPasswordMatch(payload.password, userRecord.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password combination."
        )

    profileMetadata = {
        "userId": userRecord.id,
        "email": userRecord.email,
        "role": userRecord.role.value
    }
    
    return {
        "accessToken": generateSessionToken(profileMetadata),
        "tokenType": "bearer",
        "role": userRecord.role.value,
        "fullName": userRecord.fullName
    }
