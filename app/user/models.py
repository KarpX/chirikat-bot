from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.forms.models import FormModel
from app.store.database.sql_alchemy_base import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255))

    forms: Mapped[list["FormModel"]] = relationship("FormModel", back_populates="user")

class FSMStorageModel(BaseModel):
    __tablename__ = "fsm_storage"

    key: Mapped[str] = mapped_column(String(255), primary_key=True) 
    state: Mapped[str] = mapped_column(String(255), nullable=True)
    data: Mapped[str] = mapped_column(Text, default="{}")