from datetime import date, datetime, timedelta
from decimal import Decimal
import csv, io, os, uuid
from flask import Blueprint, Response, abort, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ..extensions import db
from ..forms import CategoryForm, MovementForm, ProductForm, SaleForm, SettingsForm, SupplierForm, UserForm
from ..models import Category, Product, Sale, SaleItem, StaffProfile, StockMovement, StoreSetting, Supplier, User, UserRole
from ..utils.decorators import roles_required

bp = Blueprint("main", __name__)

def setting():
    return StoreSetting.query.first() or StoreSetting(
        store_name="FreshTrack Market",
        currency="INR",
        phone="+91 98765 43210",
        address="Indiranagar, Bengaluru, India"
    )

def choices(form):
    form.category_id.choices = [(x.id, x.name) for x in Category.query.order_by(Category.name)]
    form.supplier_id.choices = [(0, "No supplier")] + [(x.id, x.name) for x in Supplier.query.order_by(Supplier.name)]

def movement_choices(form):
    form.product_id.choices = [(x.id, f"{x.name} — {x.quantity} {x.unit}") for x in Product.query.order_by(Product.name)]

@bp.route("/")
def index():
    return redirect(url_for("main.dashboard") if current_user.is_authenticated else url_for("auth.login"))

@bp.route("/dashboard")
@login_required
def dashboard():
    products = Product.query.all()
    low = [p for p in products if p.quantity <= p.low_stock_threshold]
    soon = date.today() + timedelta(days=14)
    exp = [p for p in products if p.expiry_date and p.expiry_date <= soon]
    value = sum((Decimal(p.cost) * p.quantity for p in products), Decimal("0"))
    recent = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(7).all()
    category_rows = db.session.query(Category.name, func.sum(Product.quantity)).outerjoin(Product).group_by(Category.id).all()
    top = db.session.query(Product.name, func.coalesce(func.sum(SaleItem.quantity), 0)).outerjoin(SaleItem).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()
    days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
    trend = []
    for day in days:
        total = db.session.query(func.coalesce(func.sum(Sale.total), 0)).filter(func.date(Sale.created_at) == day.isoformat()).scalar()
        trend.append(float(total or 0))
    return render_template(
        "dashboard.html",
        store=setting(),
        product_count=len(products),
        low=low,
        expiring=exp,
        value=value,
        recent=recent,
        category_labels=[r[0] for r in category_rows],
        category_values=[int(r[1] or 0) for r in category_rows],
        top_labels=[r[0] for r in top],
        top_values=[int(r[1] or 0) for r in top],
        trend_labels=[d.strftime("%a") for d in days],
        trend_values=trend
    )

@bp.route("/products")
@login_required
def products():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", type=int)
    status = request.args.get("status", "")
    sort = request.args.get("sort", "name")
    page = request.args.get("page", 1, type=int)
    query = Product.query
    if q:
        query = query.filter(or_(Product.name.ilike(f"%{q}%"), Product.sku.ilike(f"%{q}%")))
    if category:
        query = query.filter_by(category_id=category)
    if status == "low":
        query = query.filter(Product.quantity <= Product.low_stock_threshold)
    if status == "out":
        query = query.filter(Product.quantity <= 0)
    order = {"name": Product.name.asc(), "quantity": Product.quantity.asc(), "price": Product.price.desc()}.get(sort, Product.name.asc())
    data = query.order_by(order).paginate(page=page, per_page=10, error_out=False)
    form = ProductForm()
    choices(form)
    return render_template(
        "products.html",
        products=data,
        form=form,
        categories=Category.query.order_by(Category.name).all(),
        suppliers=Supplier.query.order_by(Supplier.name).all(),
        store=setting()
    )

@bp.post("/products/create")
@login_required
@roles_required("admin", "manager")
def product_create():
    form = ProductForm()
    choices(form)
    if form.validate_on_submit():
        if Product.query.filter_by(sku=form.sku.data.strip()).first():
            flash("That SKU already exists.", "danger")
        else:
            image = None
            if form.image.data:
                image = f"{uuid.uuid4().hex}_{secure_filename(form.image.data.filename)}"
                form.image.data.save(os.path.join(current_app.config["UPLOAD_FOLDER"], image))
            p = Product(
                name=form.name.data.strip(),
                sku=form.sku.data.strip(),
                category_id=form.category_id.data,
                supplier_id=form.supplier_id.data or None,
                price=form.price.data,
                cost=form.cost.data,
                quantity=form.quantity.data,
                low_stock_threshold=form.low_stock_threshold.data,
                unit=form.unit.data,
                expiry_date=form.expiry_date.data,
                image=image
            )
            db.session.add(p)
            db.session.flush()
            if p.quantity:
                db.session.add(StockMovement(product=p, user=current_user, movement_type="in", quantity=p.quantity, note="Opening stock"))
            db.session.commit()
            flash("Product added successfully.", "success")
    else:
        flash("Please correct the product form.", "danger")
    return redirect(url_for("main.products"))

@bp.post("/products/<int:product_id>/edit")
@login_required
@roles_required("admin", "manager")
def product_edit(product_id):
    p = db.get_or_404(Product, product_id)
    form = ProductForm()
    choices(form)
    if form.validate_on_submit():
        duplicate = Product.query.filter(Product.sku == form.sku.data.strip(), Product.id != p.id).first()
        if duplicate:
            flash("That SKU already exists.", "danger")
        else:
            old = p.quantity
            p.name = form.name.data.strip()
            p.sku = form.sku.data.strip()
            p.category_id = form.category_id.data
            p.supplier_id = form.supplier_id.data or None
            p.price = form.price.data
            p.cost = form.cost.data
            p.quantity = form.quantity.data
            p.low_stock_threshold = form.low_stock_threshold.data
            p.unit = form.unit.data
            p.expiry_date = form.expiry_date.data
            if form.image.data:
                p.image = f"{uuid.uuid4().hex}_{secure_filename(form.image.data.filename)}"
                form.image.data.save(os.path.join(current_app.config["UPLOAD_FOLDER"], p.image))
            if old != p.quantity:
                db.session.add(StockMovement(product=p, user=current_user, movement_type="adjustment", quantity=p.quantity, note=f"Edited from {old}"))
            db.session.commit()
            flash("Product updated successfully.", "success")
    else:
        flash("Please check form inputs for errors.", "danger")
    return redirect(url_for("main.products"))

@bp.post("/products/<int:product_id>/delete")
@login_required
@roles_required("admin")
def product_delete(product_id):
    p = db.get_or_404(Product, product_id)
    if p.sale_items:
        flash("Products with sales history cannot be deleted.", "warning")
    else:
        db.session.delete(p)
        db.session.commit()
        flash("Product deleted.", "success")
    return redirect(url_for("main.products"))

def crud_page(model, form_class, title, endpoint, template="simple_crud.html"):
    form = form_class()
    items = model.query.order_by(model.name).all()
    return render_template(template, title=title, items=items, form=form, endpoint=endpoint, store=setting())

@bp.route("/categories")
@login_required
def categories():
    return crud_page(Category, CategoryForm, "Categories", "categories")

@bp.post("/categories/create")
@login_required
@roles_required("admin", "manager")
def category_create():
    f = CategoryForm()
    if f.validate_on_submit():
        if Category.query.filter_by(name=f.name.data.strip()).first():
            flash("Category name must be unique.", "danger")
        else:
            db.session.add(Category(name=f.name.data.strip(), description=f.description.data))
            db.session.commit()
            flash("Category added.", "success")
    else:
        flash("Please correct the form.", "danger")
    return redirect(url_for("main.categories"))

@bp.post("/categories/<int:item_id>/delete")
@login_required
@roles_required("admin")
def category_delete(item_id):
    x = db.get_or_404(Category, item_id)
    if x.products:
        flash("Move its products before deleting this category.", "warning")
    else:
        db.session.delete(x)
        db.session.commit()
        flash("Category deleted.", "success")
    return redirect(url_for("main.categories"))

@bp.route("/suppliers")
@login_required
@roles_required("admin", "manager")
def suppliers():
    return crud_page(Supplier, SupplierForm, "Suppliers", "suppliers")

@bp.post("/suppliers/create")
@login_required
@roles_required("admin", "manager")
def supplier_create():
    f = SupplierForm()
    if f.validate_on_submit():
        if Supplier.query.filter_by(name=f.name.data.strip()).first():
            flash("Company name must be unique.", "danger")
        else:
            db.session.add(Supplier(name=f.name.data.strip(), contact_name=f.contact_name.data, email=f.email.data, phone=f.phone.data, address=f.address.data))
            db.session.commit()
            flash("Supplier added.", "success")
    else:
        flash("Check the supplier details.", "danger")
    return redirect(url_for("main.suppliers"))

@bp.post("/suppliers/<int:item_id>/delete")
@login_required
@roles_required("admin")
def supplier_delete(item_id):
    x = db.get_or_404(Supplier, item_id)
    for p in x.products:
        p.supplier = None
    db.session.delete(x)
    db.session.commit()
    flash("Supplier deleted.", "success")
    return redirect(url_for("main.suppliers"))

@bp.route("/stock", methods=["GET", "POST"])
@login_required
def stock():
    form = MovementForm()
    movement_choices(form)
    if form.validate_on_submit():
        p = db.get_or_404(Product, form.product_id.data)
        qty = form.quantity.data
        if form.movement_type.data == "out" and qty > p.quantity:
            flash("Not enough stock for this movement.", "danger")
        else:
            p.quantity = qty if form.movement_type.data == "adjustment" else p.quantity + (qty if form.movement_type.data == "in" else -qty)
            db.session.add(StockMovement(product=p, user=current_user, movement_type=form.movement_type.data, quantity=qty, note=form.note.data))
            db.session.commit()
            flash("Stock movement recorded.", "success")
            return redirect(url_for("main.stock"))
    rows = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(100).all()
    return render_template("stock.html", form=form, rows=rows, store=setting())

@bp.route("/sales", methods=["GET", "POST"])
@login_required
def sales():
    form = SaleForm()
    available_products = Product.query.filter(Product.quantity > 0).order_by(Product.name).all()
    form.product_id.choices = [(x.id, f"{x.name} — {x.quantity} available") for x in available_products]

    if request.method == "POST":
        # Multi-product selection extraction
        raw_pids = request.form.getlist("product_id[]") or request.form.getlist("product_id")
        raw_qtys = request.form.getlist("quantity[]") or request.form.getlist("quantity")

        items_to_buy = []
        if raw_pids and raw_qtys:
            for pid_str, qty_str in zip(raw_pids, raw_qtys):
                try:
                    pid = int(pid_str)
                    qty = int(qty_str)
                    if pid > 0 and qty > 0:
                        items_to_buy.append((pid, qty))
                except (ValueError, TypeError):
                    continue

        if not items_to_buy:
            flash("Please select at least one product with a valid quantity.", "danger")
            return redirect(url_for("main.sales"))

        # Consolidate duplicate products in cart
        aggregated = {}
        for pid, qty in items_to_buy:
            aggregated[pid] = aggregated.get(pid, 0) + qty

        # Validate stock for all items in cart
        error_msg = None
        validated_items = []
        for pid, total_qty in aggregated.items():
            product = db.session.get(Product, pid)
            if not product:
                error_msg = f"Selected product (ID #{pid}) was not found."
                break
            if total_qty > product.quantity:
                error_msg = f"Not enough stock for {product.name}. Available: {product.quantity}, requested: {total_qty}."
                break
            validated_items.append((product, total_qty))

        if error_msg:
            flash(error_msg, "danger")
            return redirect(url_for("main.sales"))

        # Process the multi-item sale
        sale_ref = f"SALE-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
        total_price = Decimal("0.00")
        sale = Sale(reference=sale_ref, user=current_user, total=Decimal("0.00"))

        for product, qty in validated_items:
            line_total = Decimal(product.price) * qty
            total_price += line_total
            sale.items.append(SaleItem(product=product, quantity=qty, unit_price=product.price))
            product.quantity -= qty
            db.session.add(StockMovement(product=product, user=current_user, movement_type="out", quantity=qty, note=f"Sale {sale_ref}"))

        sale.total = total_price
        db.session.add(sale)
        db.session.commit()

        flash(f"Sale {sale_ref} completed successfully!", "success")
        return redirect(url_for("main.sales", latest_sale_id=sale.id))

    latest_sale_id = request.args.get("latest_sale_id", type=int)
    latest_sale = db.session.get(Sale, latest_sale_id) if latest_sale_id else None

    today_str = date.today().isoformat()
    # Auto-default start and end dates to today when visiting Sales portal without explicit URL filter params
    if "start" not in request.args and "end" not in request.args:
        start = today_str
        end = today_str
    else:
        start = request.args.get("start", "")
        end = request.args.get("end", "")

    query = Sale.query
    if start:
        query = query.filter(func.date(Sale.created_at) >= start)
    if end:
        query = query.filter(func.date(Sale.created_at) <= end)

    return render_template(
        "sales.html",
        form=form,
        sales=query.order_by(Sale.created_at.desc()).all(),
        products=available_products,
        latest_sale=latest_sale,
        start=start,
        end=end,
        today=today_str,
        store=setting()
    )

@bp.get("/sales/<int:sale_id>/pdf")
@login_required
def sale_pdf(sale_id):
    sale = db.get_or_404(Sale, sale_id)
    s = setting()

    buff = io.BytesIO()
    pdf = canvas.Canvas(buff, pagesize=letter)
    pdf.setTitle(f"Receipt-{sale.reference}")

    # Header Section
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(42, 750, s.store_name or "FreshTrack Market")

    pdf.setFont("Helvetica", 9)
    pdf.drawString(42, 736, s.address or "Indiranagar, Bengaluru, India")
    pdf.drawString(42, 724, f"Phone: {s.phone or 'N/A'} | Email: {s.email or 'N/A'}")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawRightString(570, 750, "TAX INVOICE / RECEIPT")
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(570, 734, f"Ref: {sale.reference}")
    pdf.drawRightString(570, 720, f"Date: {sale.created_at.strftime('%b %d, %Y %H:%M')}")
    pdf.drawRightString(570, 706, f"Staff: {sale.user.display_name}")

    # Separator Line
    pdf.setLineWidth(1)
    pdf.line(42, 692, 570, 692)

    # Table Header
    y = 672
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(42, y, "Item Description")
    pdf.drawString(300, y, "Qty")
    pdf.drawRightString(440, y, f"Unit Price ({s.currency})")
    pdf.drawRightString(570, y, f"Total ({s.currency})")

    y -= 8
    pdf.setLineWidth(0.5)
    pdf.line(42, y, 570, y)
    y -= 18

    # Table Content
    pdf.setFont("Helvetica", 10)
    total_qty = 0
    for item in sale.items:
        if y < 80:
            pdf.showPage()
            y = 750
            pdf.setFont("Helvetica", 10)

        p_name = item.product.name if item.product else "Product"
        line_total = Decimal(item.unit_price) * item.quantity
        total_qty += item.quantity

        pdf.drawString(42, y, p_name[:38])
        pdf.drawString(300, y, str(item.quantity))
        pdf.drawRightString(440, y, f"{item.unit_price:,.2f}")
        pdf.drawRightString(570, y, f"{line_total:,.2f}")
        y -= 18

    pdf.line(42, y + 6, 570, y + 6)
    y -= 14

    # Summary
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(42, y, f"Total Items Sold: {total_qty}")
    pdf.drawRightString(440, y, "Grand Total:")
    pdf.drawRightString(570, y, f"{s.currency} {sale.total:,.2f}")

    y -= 30
    pdf.line(42, y + 10, 570, y + 10)

    # Footer Note
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawCentredString(306, y - 10, "Thank you for shopping with FreshTrack Market!")
    pdf.drawCentredString(306, y - 24, "Computer generated sales receipt. No physical signature required.")

    pdf.save()
    buff.seek(0)
    return send_file(
        buff,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"receipt-{sale.reference}.pdf"
    )

@bp.route("/reports")
@login_required
@roles_required("admin", "manager")
def reports():
    products = Product.query.order_by(Product.name).all()
    start = request.args.get("start")
    end = request.args.get("end")
    q = Sale.query
    if start:
        q = q.filter(func.date(Sale.created_at) >= start)
    if end:
        q = q.filter(func.date(Sale.created_at) <= end)
    sales = q.order_by(Sale.created_at.desc()).all()
    return render_template(
        "reports.html",
        products=products,
        sales=sales,
        inventory_value=sum((Decimal(p.cost) * p.quantity for p in products), Decimal()),
        sales_total=sum((s.total for s in sales), Decimal()),
        store=setting()
    )

@bp.get("/reports/export/<kind>.<fmt>")
@login_required
@roles_required("admin", "manager")
def export_report(kind, fmt):
    if kind not in {"inventory", "low-stock", "sales"} or fmt not in {"csv", "pdf"}:
        abort(404)
    s = setting()
    if kind == "sales":
        headers = ["Reference", "Date", "Staff", f"Total ({s.currency})"]
        rows = [[s_item.reference, s_item.created_at.strftime("%Y-%m-%d %H:%M"), s_item.user.display_name, f"{s_item.total:,.2f}"] for s_item in Sale.query.order_by(Sale.created_at.desc()).all()]
    else:
        q = Product.query
        if kind == "low-stock":
            q = q.filter(Product.quantity <= Product.low_stock_threshold)
        headers = ["SKU", "Product", "Category", "Quantity", f"Unit cost ({s.currency})", f"Value ({s.currency})"]
        rows = [[p.sku, p.name, p.category.name, p.quantity, f"{p.cost:,.2f}", f"{(Decimal(p.cost)*p.quantity):,.2f}"] for p in q.order_by(Product.name)]

    if fmt == "csv":
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(headers)
        w.writerows(rows)
        return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={kind}.csv"})

    buff = io.BytesIO()
    pdf = canvas.Canvas(buff, pagesize=letter)
    y = 750
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(42, y, f"{kind.replace('-', ' ').title()} Report")
    y -= 30
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(42, y, " | ".join(headers))
    y -= 16
    pdf.setFont("Helvetica", 8)
    for row in rows:
        if y < 45:
            pdf.showPage()
            y = 750
            pdf.setFont("Helvetica", 8)
        pdf.drawString(42, y, " | ".join(map(str, row))[:115])
        y -= 14
    pdf.save()
    buff.seek(0)
    return send_file(buff, mimetype="application/pdf", as_attachment=True, download_name=f"{kind}.pdf")

@bp.route("/settings", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def settings():
    s = StoreSetting.query.first()
    if not s:
        s = StoreSetting()
        db.session.add(s)
        db.session.commit()
    form = SettingsForm(obj=s)
    if form.validate_on_submit():
        form.populate_obj(s)
        db.session.commit()
        flash("Store settings saved.", "success")
        return redirect(url_for("main.settings"))
    users = User.query.order_by(User.created_at.desc()).all()
    user_form = UserForm()
    return render_template("settings.html", form=form, users=users, user_form=user_form, store=s)

@bp.post("/users/create")
@login_required
@roles_required("admin")
def user_create():
    f = UserForm()
    if f.validate_on_submit() and not User.query.filter_by(email=f.email.data.lower()).first():
        u = User(email=f.email.data.lower())
        u.set_password(f.password.data)
        u.profile = StaffProfile(display_name=f.display_name.data)
        u.role_record = UserRole(role=f.role.data)
        db.session.add(u)
        db.session.commit()
        flash("Team member added.", "success")
    else:
        flash("Check the team member details.", "danger")
    return redirect(url_for("main.settings"))
