# app/deps.py
from bson import ObjectId
from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app import crud, database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, crud.SECRET_KEY, algorithms=[crud.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def get_object_id_or_404(param_name: str, description: str):
    def dependency(
        obj_id: str = Path(..., alias=param_name, description=description),
    ) -> ObjectId:
        if not ObjectId.is_valid(obj_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        return ObjectId(obj_id)

    return dependency
