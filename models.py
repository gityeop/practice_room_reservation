from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    cancel_count = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    # 토큰 관련 필드 추가
    token = db.Column(db.String(100), unique=True, nullable=True)
    token_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self, expires_in=86400):
        """Supabase와 함께 사용하기 위한 새 토큰을 생성하지만 데이터베이스에 저장하지는 않음"""
        # 새 토큰 생성
        token = secrets.token_hex(32)
        return token
        
    def get_token(self, expires_in=86400):
        """SQLite 호환을 위해 유지. 기존 토큰이 있고 만료되지 않았으면 기존 토큰 반환, 아니면 새 토큰 생성하고 저장"""
        now = datetime.utcnow()
        if self.token and self.token_expiration and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        # 새 토큰 생성
        self.token = secrets.token_hex(32)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.commit()
        return self.token

    def revoke_token(self):
        """토큰 무효화 - SQLite 호환을 위해 유지"""
        self.token = None
        self.token_expiration = None
        db.session.commit()
        
    @staticmethod
    def check_token(token):
        """토큰으로 사용자 찾기 - SQLite 호환을 위해 유지"""
        if not token:
            return None
            
        user = User.query.filter_by(token=token).first()
        if not user or not user.token_expiration or user.token_expiration < datetime.utcnow():
            return None
        return user

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    purpose = db.Column(db.Text, nullable=True)

class BlockedTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(200), nullable=True)  # 수업, 회의 등
