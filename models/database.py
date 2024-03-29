from enum import Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Boolean, ForeignKey, Integer, String, CheckConstraint, UniqueConstraint, DateTime, Float, Enum as sqlEnum

Base = declarative_base()

class HttpVerb(Enum):
    get = 'get'
    post = 'post'
    head = 'head'
    put = 'put'
    patch = 'patch'
    connect = 'connect'
    options = 'options'
    trace = 'trace'
    delete = 'delete'

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)

    goals = relationship("Goal", back_populates="user", cascade="all, delete")
    auth_tokens = relationship("Auth", back_populates="user", cascade="all, delete")
    new_password_requests = relationship("NewPasswordReq", back_populates="user", cascade="all, delete")

class Goal(Base):
    __tablename__ = "goal"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String, nullable=False, unique=True)
    status = Column(Integer, CheckConstraint("status in (-1, 0, 1)"), nullable=False, default=-1)
    start_datetime = Column(DateTime)
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

class Auth(Base):
    __tablename__ = "auth"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    app_name = Column(String)
    signature_used = Column(Integer, ForeignKey("secret_signature.id"), nullable=False)
    creation_date = Column(DateTime, nullable=False)
    token_value = Column(String, nullable=False, unique=True)
    expiration_date = Column(DateTime, nullable=False)
    last_time_used = Column(DateTime, nullable=False)
    user_profile_access = Column(Boolean, nullable=False, default=False)
    samples_access = Column(Boolean, nullable=False, default=False)
    goals_access = Column(Boolean, nullable=False, default=False)
    stats_access = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="auth_tokens")
    signature = relationship("SecretSignature", back_populates="token")

class NewPasswordReq(Base):
    __tablename__ = "new_password_req"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    change_req_id = Column(String, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    change_applied = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="new_password_requests")

class AdminManagement(Base):
    __tablename__ = "admin_management"
    id = Column(Integer, primary_key=True)
    edit_date = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    manage_doc = Column(Boolean, nullable=False)
    manage_user = Column(Boolean, nullable=False)
    manage_backup = Column(Boolean, nullable=False)

class SecretSignature(Base):
    __tablename__ = "secret_signature"
    id = Column(Integer, primary_key=True)
    secret_value = Column(String, nullable=False, unique=True)
    generation_date = Column(DateTime, nullable=False)

    token = relationship("Auth", back_populates="signature", cascade="all, delete")

class DocResource(Base):
    __tablename__ = "doc_resource"
    id = Column(Integer, primary_key=True)
    resource_name = Column(String, nullable=False, unique=True)
    description = Column(String)
    admin_privilege = Column(Boolean, nullable=False)

class DocFeature(Base):
    __tablename__ = "doc_feature"
    __table_args__ = (
        UniqueConstraint("http_verb", "uri"),
    )
    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey("doc_resource.id"), nullable=False)
    title = Column(String, nullable=False, unique=True)
    description = Column(String)
    http_verb = Column(sqlEnum(HttpVerb), nullable=False)
    uri = Column(String, nullable=False)
    admin_privilege = Column(Boolean, nullable=False)
    available = Column(Boolean, nullable=False, default=False)

class DocSection(Base):
    __tablename__ = "doc_section"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)

class DocContentBlock(Base):
    __tablename__ = "doc_content_block"
    id = Column(Integer, primary_key=True)
    doc_section_id = Column(Integer, ForeignKey("doc_section.id"), nullable=False)
    title = Column(String, nullable=False, unique=True)
    content = Column(String, nullable=False, unique=True)