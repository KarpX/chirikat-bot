from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.forms.models import FormModel
from app.store.database.sql_alchemy_base import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255))

    forms: Mapped[list["FormModel"]] = relationship("FormModel", back_populates="user")