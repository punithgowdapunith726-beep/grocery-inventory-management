from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


def utcnow(): return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    profile = db.relationship("StaffProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    role_record = db.relationship("UserRole", back_populates="user", uselist=False, cascade="all, delete-orphan")
    movements = db.relationship("StockMovement", back_populates="user")
    sales = db.relationship("Sale", back_populates="user")
    @property
    def is_active(self): return self.is_active_account
    @property
    def role(self): return self.role_record.role if self.role_record else "staff"
    @property
    def display_name(self): return self.profile.display_name if self.profile else self.email.split("@")[0]
    def set_password(self, value): self.password_hash = generate_password_hash(value)
    def check_password(self, value): return check_password_hash(self.password_hash, value)

class StaffProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(255))
    user = db.relationship("User", back_populates="profile")

class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    user = db.relationship("User", back_populates="role_record")

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(300))
    products = db.relationship("Product", back_populates="category")

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    contact_name = db.Column(db.String(100)); email = db.Column(db.String(180)); phone = db.Column(db.String(50)); address = db.Column(db.String(300))
    products = db.relationship("Product", back_populates="supplier")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    sku = db.Column(db.String(80), unique=True, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"))
    price = db.Column(db.Numeric(12,2), nullable=False, default=0)
    cost = db.Column(db.Numeric(12,2), nullable=False, default=0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=10)
    unit = db.Column(db.String(30), nullable=False, default="unit")
    expiry_date = db.Column(db.Date)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    category = db.relationship("Category", back_populates="products")
    supplier = db.relationship("Supplier", back_populates="products")
    movements = db.relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")
    sale_items = db.relationship("SaleItem", back_populates="product")
    @property
    def stock_status(self):
        return "out" if self.quantity <= 0 else ("low" if self.quantity <= self.low_stock_threshold else "healthy")

class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(300))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    product = db.relationship("Product", back_populates="movements"); user = db.relationship("User", back_populates="movements")

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(40), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total = db.Column(db.Numeric(12,2), nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    user = db.relationship("User", back_populates="sales")
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12,2), nullable=False)
    sale = db.relationship("Sale", back_populates="items"); product = db.relationship("Product", back_populates="sale_items")

class StoreSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(120), nullable=False, default="FreshTrack Market")
    email = db.Column(db.String(180)); phone = db.Column(db.String(50)); address = db.Column(db.String(300)); currency = db.Column(db.String(10), default="INR")
