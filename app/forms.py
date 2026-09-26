from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, DateField, DecimalField, EmailField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    email=EmailField("Email",validators=[DataRequired(),Email()]); password=PasswordField("Password",validators=[DataRequired()]); remember=BooleanField("Remember me"); submit=SubmitField("Sign in")
class RegisterForm(FlaskForm):
    display_name=StringField("Full name",validators=[DataRequired(),Length(max=100)]); email=EmailField("Email",validators=[DataRequired(),Email()]); password=PasswordField("Password",validators=[DataRequired(),Length(min=8)]); confirm=PasswordField("Confirm password",validators=[DataRequired(),EqualTo("password")]); submit=SubmitField("Create account")
class ProductForm(FlaskForm):
    name=StringField("Product name",validators=[DataRequired(),Length(max=150)]); sku=StringField("SKU / Barcode",validators=[DataRequired(),Length(max=80)]); category_id=SelectField("Category",coerce=int,validators=[DataRequired()]); supplier_id=SelectField("Supplier",coerce=int,validators=[Optional()]); price=DecimalField("Selling price",places=2,validators=[DataRequired(),NumberRange(min=0)]); cost=DecimalField("Unit cost",places=2,validators=[DataRequired(),NumberRange(min=0)]); quantity=IntegerField("Opening quantity",validators=[DataRequired(),NumberRange(min=0)]); low_stock_threshold=IntegerField("Low-stock threshold",validators=[DataRequired(),NumberRange(min=0)]); unit=StringField("Unit",validators=[DataRequired()]); expiry_date=DateField("Expiry date",validators=[Optional()]); image=FileField("Product image",validators=[FileAllowed(["jpg","jpeg","png","webp"],"Images only")]); submit=SubmitField("Save product")
class CategoryForm(FlaskForm):
    name=StringField("Name",validators=[DataRequired(),Length(max=100)]); description=TextAreaField("Description",validators=[Optional(),Length(max=300)]); submit=SubmitField("Save category")
class SupplierForm(FlaskForm):
    name=StringField("Company",validators=[DataRequired()]); contact_name=StringField("Contact"); email=EmailField("Email",validators=[Optional(),Email()]); phone=StringField("Phone"); address=TextAreaField("Address"); submit=SubmitField("Save supplier")
class MovementForm(FlaskForm):
    product_id=SelectField("Product",coerce=int,validators=[DataRequired()]); movement_type=SelectField("Type",choices=[("in","Stock in"),("out","Stock out"),("adjustment","Set quantity")]); quantity=IntegerField("Quantity",validators=[DataRequired(),NumberRange(min=0)]); note=StringField("Note",validators=[Optional(),Length(max=300)]); submit=SubmitField("Record movement")
class SaleForm(FlaskForm):
    product_id=SelectField("Product",coerce=int,validators=[DataRequired()]); quantity=IntegerField("Quantity",validators=[DataRequired(),NumberRange(min=1)]); submit=SubmitField("Complete sale")
class UserForm(FlaskForm):
    display_name=StringField("Name",validators=[DataRequired()]); email=EmailField("Email",validators=[DataRequired(),Email()]); password=PasswordField("Temporary password",validators=[DataRequired(),Length(min=8)]); role=SelectField("Role",choices=[("admin","Admin"),("manager","Manager"),("staff","Staff")]); submit=SubmitField("Add user")
class SettingsForm(FlaskForm):
    store_name=StringField("Store name",validators=[DataRequired()]); email=EmailField("Store email",validators=[Optional(),Email()]); phone=StringField("Phone"); address=TextAreaField("Address"); currency=SelectField("Currency",choices=[("INR","INR — ₹"),("USD","USD — $"),("EUR","EUR — €"),("GBP","GBP — £")],default="INR"); submit=SubmitField("Save settings")
