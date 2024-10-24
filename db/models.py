from typing import Annotated, List
import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, PickleType, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, relationship, mapped_column


Base = declarative_base()
intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]

class User(Base):
    __tablename__ = 'users'
    id = Column(
        Integer, 
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True
    )
    telegram_id = Column(BigInteger, index=True)
    telegram_handle = Column(String, index=True)
    name = Column(String)
    phone_number = Column(String)
    address: Mapped[str]
    postal_code: Mapped[str]
    cart: Mapped['Cart'] = relationship()
    created_at: Mapped[created_at]


class Product(Base):
    __tablename__ = 'products'
    id = Column(
        Integer, 
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True
    )
    name = Column(String, index=True)
    description = Column(String)
    categories = Column(String)
    stock = Column(Integer)
    picture = Column(String)
    price = Column(BigInteger)
    variant = Column(String)


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[intpk]
    customer_id = mapped_column(ForeignKey('users.id'))
    items: Mapped[list['OrderItem']] = relationship()
    status: Mapped[str]
    products_cost: Mapped[int]
    delivery_cost: Mapped[int]
    total: Mapped[int]
    tracking_number: Mapped[str]
    created_at: Mapped[created_at]



class OrderItem(Base):
    __tablename__ = 'order_items'
    id: Mapped[intpk]
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int]


class Cart(Base):
    __tablename__ = 'carts'
    id: Mapped[intpk]
    # owner: Mapped['User'] = relationship(back_populates='cart')
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    items: Mapped[list['CartItem']] = relationship()
    total: Mapped[int]


class CartItem(Base):
    __tablename__ = 'cart_items'
    id: Mapped[intpk]
    cart_id: Mapped[int] = mapped_column(ForeignKey('carts.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int]
