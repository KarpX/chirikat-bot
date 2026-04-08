import typing
from sqlalchemy import TIMESTAMP, BigInteger, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.store.database.sql_alchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.user.models import UserModel


class FormModel(BaseModel):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    city: Mapped[int] = mapped_column(Integer, ForeignKey("cities.id"), nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="forms")
    images: Mapped[list["FormImageModel"]] = relationship("FormImageModel", back_populates="form")
    liked_form: Mapped[list["FormLikeModel"]] = relationship("FormLikeModel", foreign_keys="[FormLikeModel.liked_form_id]", back_populates="liked_form")
    like_from: Mapped[list["FormLikeModel"]] = relationship("FormLikeModel", foreign_keys="[FormLikeModel.like_from]", back_populates="like_from_form")
    city_rel: Mapped["CityModel"] = relationship("CityModel", back_populates="forms")
    matches_as_form1: Mapped[list["MatchModel"]] = relationship("MatchModel", foreign_keys="[MatchModel.form1_id]", back_populates="form1")
    matches_as_form2: Mapped[list["MatchModel"]] = relationship("MatchModel", foreign_keys="[MatchModel.form2_id]", back_populates="form2")

class FormImageModel(BaseModel):
    __tablename__ = "form_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_id: Mapped[int] = mapped_column(Integer, ForeignKey("forms.id"), nullable=False)
    file_id: Mapped[str] = mapped_column(Text, nullable=False)

    form: Mapped["FormModel"] = relationship("FormModel", back_populates="images")

class FormLikeModel(BaseModel):
    __tablename__ = "form_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    liked_form_id: Mapped[int] = mapped_column(Integer, ForeignKey("forms.id"), nullable=False)
    like_from: Mapped[int] = mapped_column(Integer, ForeignKey("forms.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)

    liked_form: Mapped["FormModel"] = relationship("FormModel", foreign_keys=[liked_form_id], back_populates="liked_form")
    like_from_form: Mapped["FormModel"] = relationship("FormModel", foreign_keys=[like_from], back_populates="like_from")

class MatchModel(BaseModel):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form1_id: Mapped[int] = mapped_column(Integer, ForeignKey("forms.id"), nullable=False)
    form2_id: Mapped[int] = mapped_column(Integer, ForeignKey("forms.id"), nullable=False)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)

    form1: Mapped["FormModel"] = relationship("FormModel", foreign_keys=[form1_id], back_populates="matches_as_form1")
    form2: Mapped["FormModel"] = relationship("FormModel", foreign_keys=[form2_id], back_populates="matches_as_form2")

class CityModel(BaseModel):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    forms: Mapped[list["FormModel"]] = relationship("FormModel", back_populates="city_rel")