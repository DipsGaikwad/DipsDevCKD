from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import get_db
from backend.models import User

_passwords=PasswordHash.recommended()
_bearer=HTTPBearer(auto_error=False)
def hash_password(password:str)->str: return _passwords.hash(password)
def verify_password(password:str,encoded:str)->bool:
    try: return _passwords.verify(password,encoded)
    except Exception: return False

def create_token(user:User)->str:
    now=datetime.now(timezone.utc)
    payload={'sub':str(user.user_id),'role':user.role,'iat':now,'exp':now+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload,settings.JWT_SECRET_KEY,algorithm='HS256')

def get_current_user(credentials:HTTPAuthorizationCredentials|None=Depends(_bearer),db:Session=Depends(get_db))->User:
    if not credentials: raise HTTPException(status_code=401,detail='Sign in required',headers={'WWW-Authenticate':'Bearer'})
    try:
        payload=jwt.decode(credentials.credentials,settings.JWT_SECRET_KEY,algorithms=['HS256'])
        uid=int(payload.get('sub','0'))
    except Exception: raise HTTPException(status_code=401,detail='Invalid or expired access token')
    user=db.get(User,uid)
    if not user or user.account_status!='APPROVED': raise HTTPException(status_code=403,detail='Account is not approved or is suspended')
    return user

def require_roles(*roles):
    def checker(user:User=Depends(get_current_user)):
        if user.role not in roles: raise HTTPException(status_code=403,detail='You do not have permission to perform this action')
        return user
    return checker

def ensure_user_can_access(patient_id:str,user:User):
    # Starter project has no doctor-patient assignment table; approved clinicians have workspace-level access.
    # Add assignments before deploying across independent clinical teams.
    return True
