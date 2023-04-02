from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, CheckConstraint, DateTime, Float

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    password = Column(String, nullable=False)

    goals = relationship("Goal", back_populates="user")

class Goal(Base):
    __tablename__ = "goal"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(Integer, CheckConstraint("status in (-1, 0, 1)"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime)
    average_target = Column(Integer)
    trend_target = Column(Integer, CheckConstraint("trend_target in (-1, 0, 1)"))
    minimum = Column(Integer)
    maximum = Column(Integer)
    stat_range = Column(Integer)
    mean = Column(Float)
    variance = Column(Float)
    std_dev = Column(Float)
    overall_samples_size = Column(Integer)
    first_quart = Column(Integer)
    second_quart = Column(Integer)
    third_quart = Column(Integer)
    median = Column(Float)

    user = relationship("User", back_populates="goals")