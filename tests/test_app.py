from app import create_app
from app.extensions import db
from app.models import Category, Product, Sale, StaffProfile, Supplier, User, UserRole

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = '/tmp/grocery-test-uploads'

def make_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        u = User(email='admin@test.com')
        u.set_password('Password1!')
        u.profile = StaffProfile(display_name='Punith')
        u.role_record = UserRole(role='admin')

        m = User(email='manager@test.com')
        m.set_password('Password1!')
        m.profile = StaffProfile(display_name='Punith')
        m.role_record = UserRole(role='manager')

        c = Category(name='Produce')
        s = Supplier(name='Farm')
        p1 = Product(name='Apple', sku='A1', category=c, supplier=s, price=20.0, cost=10.0, quantity=100, low_stock_threshold=10, unit='kg')
        p2 = Product(name='Banana', sku='B1', category=c, supplier=s, price=15.0, cost=8.0, quantity=150, low_stock_threshold=15, unit='kg')

        db.session.add_all([u, m, c, s, p1, p2])
        db.session.commit()
    return app

def login(c, email='admin@test.com', password='Password1!'):
    return c.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

def test_dashboard():
    c = make_app().test_client()
    r = login(c)
    assert r.status_code == 200 and b'Good day, Punith' in r.data

def test_sale_deducts():
    app = make_app()
    c = app.test_client()
    login(c)
    r = c.post('/sales', data={'product_id': 1, 'quantity': 2}, follow_redirects=True)
    assert b'completed successfully' in r.data
    with app.app_context():
        assert db.session.get(Product, 1).quantity == 98

def test_multi_item_sale():
    app = make_app()
    c = app.test_client()
    login(c)
    r = c.post('/sales', data={
        'product_id[]': ['1', '2'],
        'quantity[]': ['5', '10']
    }, follow_redirects=True)
    assert b'completed successfully' in r.data
    with app.app_context():
        assert db.session.get(Product, 1).quantity == 95
        assert db.session.get(Product, 2).quantity == 140

def test_sale_pdf_generation():
    app = make_app()
    c = app.test_client()
    login(c)
    c.post('/sales', data={'product_id': 1, 'quantity': 3}, follow_redirects=True)
    with app.app_context():
        sale = Sale.query.first()
        sale_id = sale.id

    r = c.get(f'/sales/{sale_id}/pdf')
    assert r.status_code == 200
    assert r.mimetype == 'application/pdf'
    assert b'%PDF' in r.data

def test_prevent_oversale():
    c = make_app().test_client()
    login(c)
    r = c.post('/sales', data={'product_id': 1, 'quantity': 999}, follow_redirects=True)
    assert b'Not enough stock' in r.data
