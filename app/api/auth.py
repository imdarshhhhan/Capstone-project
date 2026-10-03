import firebase_admin
from firebase_admin import auth as firebaseAuth
from firebase_admin import credentials as firebaseCredentials
from firebase_admin.exceptions import FirebaseError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import settings
from db.models import User, UserRole
from db.sessions import getDb


router = APIRouter(prefix="/auth", tags=["Federated User Authentication"])
oauth2Scheme = OAuth2PasswordBearer(tokenUrl="auth/verify-sync-login")


class FirebaseSignupPayload(BaseModel):
    idToken: str
    fullName: str = Field(min_length=1)
    roleSelection: UserRole


class FirebaseLoginPayload(BaseModel):
    idToken: str


def _firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        project_id = settings.FIREBASE_PROJECT_ID
        if not project_id:
            raise RuntimeError(
                "Firebase Admin requires FIREBASE_PROJECT_ID to verify login tokens."
            )
        client_email = settings.FIREBASE_CLIENT_EMAIL
        private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
        if client_email and private_key:
            credential = firebaseCredentials.Certificate(
                {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key": private_key,
                    "client_email": client_email,
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            )
            return firebase_admin.initialize_app(
                credential, options={"projectId": project_id}
            )
        return firebase_admin.initialize_app(options={"projectId": project_id})


def _verify_firebase_token(id_token: str) -> dict:
    try:
        return firebaseAuth.verify_id_token(id_token, app=_firebase_app())
    except (ValueError, FirebaseError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The Firebase sign-in token is invalid or expired.",
        ) from exc


def _serialize_user(user: User) -> dict:
    return {
        "userId": user.id,
        "role": user.role.value,
        "email": user.email,
        "fullName": user.fullName,
    }


def verifyFirebaseTokenDependency(
    token: str = Depends(oauth2Scheme), db: Session = Depends(getDb)
) -> dict:
    decoded_token = _verify_firebase_token(token)
    user = db.query(User).filter(User.firebaseUid == decoded_token["uid"]).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This Firebase account has not been registered in the application.",
        )
    return _serialize_user(user)


@router.post("/verify-sync-signup", status_code=status.HTTP_201_CREATED)
def verifySyncSignup(payload: FirebaseSignupPayload, db: Session = Depends(getDb)):
    decoded_token = _verify_firebase_token(payload.idToken)
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    if not firebase_uid or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The Firebase account must include a user ID and email address.",
        )

    existing_user = (
        db.query(User).filter(User.firebaseUid == firebase_uid).first()
    )
    if existing_user is not None:
        return _serialize_user(existing_user)

    email = email.strip().lower()
    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    full_name = payload.fullName.strip()
    if not full_name:
        full_name = decoded_token.get("name") or email.split("@", maxsplit=1)[0]

    user = User(
        firebaseUid=firebase_uid,
        email=email,
        fullName=full_name,
        role=payload.roleSelection,
        avatarUrl=decoded_token.get("picture"),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing_user = (
            db.query(User).filter(User.firebaseUid == firebase_uid).first()
        )
        if existing_user is not None:
            return _serialize_user(existing_user)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc

    db.refresh(user)
    return _serialize_user(user)


@router.post("/verify-sync-login")
def verifySyncLogin(payload: FirebaseLoginPayload, db: Session = Depends(getDb)):
    decoded_token = _verify_firebase_token(payload.idToken)
    firebase_uid = decoded_token["uid"]
    user = db.query(User).filter(User.firebaseUid == firebase_uid).first()

    if user is None:
        email = decoded_token.get("email")
        if email and decoded_token.get("email_verified") is True:
            existing_user = (
                db.query(User).filter(User.email == email.strip().lower()).first()
            )
            if existing_user is not None and existing_user.firebaseUid is None:
                existing_user.firebaseUid = firebase_uid
                try:
                    db.commit()
                except IntegrityError as exc:
                    db.rollback()
                    user = (
                        db.query(User)
                        .filter(User.firebaseUid == firebase_uid)
                        .first()
                    )
                    if user is None:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="This account is already linked to another sign-in.",
                        ) from exc
                else:
                    db.refresh(existing_user)
                    user = existing_user

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No application account is registered for this Firebase user. Create an account first, or verify the email address on your existing account.",
        )
    return _serialize_user(user)
