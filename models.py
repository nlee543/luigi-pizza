from sqlalchemy import Boolean, Integer, String, false
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    dine_in_name: Mapped[str] = mapped_column(String, nullable=False)
    admin: Mapped[bool] = mapped_column(
        Boolean(create_constraint=True, name="admin_boolean"),
        nullable=False,
        default=False,
        server_default=false(),
    )
