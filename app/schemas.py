from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
