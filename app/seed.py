import click
from datetime import date, timedelta
from decimal import Decimal
from flask.cli import with_appcontext
from .extensions import db
from .models import Category, Product, Sale, SaleItem, StaffProfile, StockMovement, StoreSetting, Supplier, User, UserRole

@click.command("seed")
@with_appcontext
def seed_command():
    db.drop_all(); db.create_all()
    users=[]
    user_credentials = [
        ("Punith", "admin@freshtrack.example", "Admin123!", "admin"),
        ("Punith", "manager@freshtrack.example", "Manager123!", "manager"),
        ("Noah Williams", "staff@freshtrack.example", "Staff123!", "staff")
    ]
    for name, email, password, role in user_credentials:
        u = User(email=email)
        u.set_password(password)
        u.profile = StaffProfile(display_name=name)
        u.role_record = UserRole(role=role)
        db.session.add(u)
        users.append(u)

    cats = [
        Category(name=n, description=d) for n, d in [
            ("Produce", "Fresh fruits, vegetables, and herbs"),
            ("Dairy & Eggs", "Milk, cheese, butter, eggs, and chilled goods"),
            ("Pantry Essentials", "Grains, pulses, oils, spices, and staples"),
            ("Bakery", "Fresh bread, rolls, pastries, and baked goods"),
            ("Beverages", "Juices, tea, coffee, and refreshing drinks"),
            ("Snacks & Packaged", "Nuts, dried fruits, biscuits, and confectionery")
        ]
    ]

    suppliers = [
        Supplier(name="Green Valley Farms", contact_name="Anand", email="orders@greenvalley.example", phone="555-0142", address="78 Farm Road, Bengaluru"),
        Supplier(name="Northstar Foods", contact_name="Ramesh", email="sales@northstar.example", phone="555-0186", address="12 Logistics Park, Mumbai"),
        Supplier(name="Daily Bake Co.", contact_name="Praveen", email="hello@dailybake.example", phone="555-0118", address="45 Baker Street, New Delhi"),
        Supplier(name="Fresh Springs Beverage Co.", contact_name="Ananya Sharma", email="orders@freshsprings.example", phone="555-0199", address="99 Industrial Estate, Mysuru")
    ]
    db.session.add_all(cats + suppliers)
    db.session.flush()

    # Product specs: (name, sku, category_index, supplier_index, price, cost, quantity, low_threshold, unit, expiry_date)
    specs = [
        ("Organic Bananas", "PRD-1001", 0, 0, "60.00", "40.00", 450, 50, "kg", None),
        ("Royal Gala Apples", "PRD-1002", 0, 0, "180.00", "120.00", 300, 40, "kg", date.today() + timedelta(days=20)),
        ("Fresh Farm Tomatoes", "PRD-1003", 0, 0, "40.00", "25.00", 500, 60, "kg", date.today() + timedelta(days=10)),
        ("Baby Spinach 200g", "PRD-1004", 0, 0, "50.00", "30.00", 200, 30, "pack", date.today() + timedelta(days=6)),
        ("Hass Avocados", "PRD-1005", 0, 0, "120.00", "80.00", 180, 25, "unit", date.today() + timedelta(days=8)),

        ("Whole Milk 1L", "DRY-2001", 1, 1, "65.00", "45.00", 400, 50, "bottle", date.today() + timedelta(days=12)),
        ("Free Range Farm Eggs", "DRY-2002", 1, 1, "140.00", "95.00", 250, 30, "pack", date.today() + timedelta(days=18)),
        ("Amul Cheddar Cheese 200g", "DRY-2003", 1, 1, "165.00", "120.00", 220, 25, "pack", date.today() + timedelta(days=60)),
        ("Greek Style Yogurt 500g", "DRY-2004", 1, 1, "110.00", "75.00", 190, 20, "tub", date.today() + timedelta(days=14)),
        ("Pure Cow Ghee 500ml", "DRY-2005", 1, 1, "380.00", "290.00", 150, 15, "jar", date.today() + timedelta(days=180)),

        ("Premium Basmati Rice 5kg", "PNT-3001", 2, 1, "650.00", "480.00", 350, 40, "bag", date.today() + timedelta(days=365)),
        ("Extra Virgin Olive Oil 1L", "PNT-3002", 2, 1, "950.00", "720.00", 160, 20, "bottle", date.today() + timedelta(days=300)),
        ("Whole Wheat Atta 10kg", "PNT-3003", 2, 1, "420.00", "320.00", 280, 35, "bag", date.today() + timedelta(days=120)),
        ("Organic Turmeric Powder 250g", "PNT-3004", 2, 1, "95.00", "60.00", 300, 30, "pack", date.today() + timedelta(days=240)),
        ("Durum Wheat Pasta 500g", "PNT-3005", 2, 1, "120.00", "80.00", 400, 50, "pack", date.today() + timedelta(days=360)),

        ("Fresh Artisan Sourdough", "BAK-4001", 3, 2, "140.00", "85.00", 120, 20, "loaf", date.today() + timedelta(days=4)),
        ("Whole Wheat Sandwich Bread", "BAK-4002", 3, 2, "50.00", "32.00", 250, 30, "loaf", date.today() + timedelta(days=5)),
        ("Butter Croissants 4-Pack", "BAK-4003", 3, 2, "180.00", "110.00", 100, 15, "pack", date.today() + timedelta(days=3)),

        ("Pure Tender Coconut Water 200ml", "BEV-5001", 4, 3, "50.00", "30.00", 600, 60, "bottle", date.today() + timedelta(days=90)),
        ("Organic Green Tea 100g", "BEV-5002", 4, 3, "220.00", "150.00", 210, 25, "box", date.today() + timedelta(days=365)),
        ("Fresh Orange Juice 1L", "BEV-5003", 4, 3, "160.00", "105.00", 280, 30, "bottle", date.today() + timedelta(days=15)),

        ("Roasted Salted Almonds 250g", "SNK-6001", 5, 1, "290.00", "210.00", 240, 25, "pouch", date.today() + timedelta(days=180)),
        ("Dark Chocolate 70% 100g", "SNK-6002", 5, 1, "150.00", "95.00", 320, 35, "bar", date.today() + timedelta(days=270)),
        ("Multigrain Digestives 300g", "SNK-6003", 5, 2, "85.00", "55.00", 380, 40, "pack", date.today() + timedelta(days=150)),
        ("Honey Roasted Cashews 200g", "SNK-6004", 5, 1, "320.00", "230.00", 200, 20, "pouch", date.today() + timedelta(days=180))
    ]

    products = []
    for name, sku, ci, si, price, cost, qty, low, unit, expiry in specs:
        p = Product(
            name=name,
            sku=sku,
            category=cats[ci],
            supplier=suppliers[si],
            price=Decimal(price),
            cost=Decimal(cost),
            quantity=qty,
            low_stock_threshold=low,
            unit=unit,
            expiry_date=expiry
        )
        db.session.add(p)
        products.append(p)

    db.session.flush()

    for p in products:
        db.session.add(StockMovement(product=p, user=users[0], movement_type="in", quantity=p.quantity, note="Seed opening stock"))

    # Initial sample multi-item sales
    sale_data = [
        [(products[0], 10), (products[5], 4), (products[10], 2)],
        [(products[1], 5), (products[6], 2), (products[15], 3)],
        [(products[18], 12), (products[21], 4)]
    ]

    for idx, items_list in enumerate(sale_data):
        total_amount = sum(prod.price * q for prod, q in items_list)
        s = Sale(reference=f"SALE-DEMO-{idx+1:03}", user=users[2], total=total_amount)
        for prod, q in items_list:
            s.items.append(SaleItem(product=prod, quantity=q, unit_price=prod.price))
            prod.quantity -= q
            db.session.add(StockMovement(product=prod, user=users[2], movement_type="out", quantity=q, note=s.reference))
        db.session.add(s)

    db.session.add(StoreSetting(
        store_name="FreshTrack Market",
        email="hello@freshtrack.example",
        phone="+91 98765 43210",
        address="142 MG Road, Indiranagar, Bengaluru, India",
        currency="INR"
    ))
    db.session.commit()
    click.echo("Seeded FreshTrack with abundant stock & INR currency. Admin/Manager: Punith (admin@freshtrack.example / Admin123!)")
