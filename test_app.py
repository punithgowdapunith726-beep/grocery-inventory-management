import requests, re, sys

s = requests.Session()
ok = 0
fail = 0

def test(num, desc, condition):
    global ok, fail
    if condition:
        print(f"  PASS {num}. {desc}")
        ok += 1
    else:
        print(f"  FAIL {num}. {desc}")
        fail += 1

# Test 1: Login page loads
r = s.get("http://127.0.0.1:5050/auth/login")
test(1, f"Login page loads (status={r.status_code})", r.status_code == 200 and "Sign in" in r.text)

# Test 2: Login POST
token_match = re.search(r'name="csrf_token".*?value="([^"]+)"', r.text)
if token_match:
    csrf = token_match.group(1)
    r = s.post("http://127.0.0.1:5050/auth/login", data={
        "csrf_token": csrf,
        "email": "admin@freshtrack.example",
        "password": "Admin123!",
        "remember": "y"
    }, allow_redirects=True)
    test(2, f"Login succeeds -> dashboard (status={r.status_code})", r.status_code == 200 and "dashboard" in r.url)
else:
    test(2, "Login - CSRF token found", False)

# Test 3: Dashboard
r = s.get("http://127.0.0.1:5050/dashboard")
test(3, f"Dashboard loads (status={r.status_code})", r.status_code == 200 and "Total products" in r.text and "Punith" in r.text)

# Test 4: Products
r = s.get("http://127.0.0.1:5050/products")
test(4, f"Products page (status={r.status_code})", r.status_code == 200 and "Products" in r.text)

# Test 5: Stock
r = s.get("http://127.0.0.1:5050/stock")
test(5, f"Stock page (status={r.status_code})", r.status_code == 200 and "Record movement" in r.text)

# Test 6: Sales
r = s.get("http://127.0.0.1:5050/sales")
test(6, f"Sales page (status={r.status_code})", r.status_code == 200 and "Sales Portal" in r.text)

# Test 7: Categories
r = s.get("http://127.0.0.1:5050/categories")
test(7, f"Categories page (status={r.status_code})", r.status_code == 200 and "Produce" in r.text)

# Test 8: Suppliers
r = s.get("http://127.0.0.1:5050/suppliers")
test(8, f"Suppliers page (status={r.status_code})", r.status_code == 200 and "Green Valley" in r.text)

# Test 9: Reports
r = s.get("http://127.0.0.1:5050/reports")
test(9, f"Reports page (status={r.status_code})", r.status_code == 200 and "Inventory valuation" in r.text)

# Test 10: Settings
r = s.get("http://127.0.0.1:5050/settings")
test(10, f"Settings page (status={r.status_code})", r.status_code == 200 and "Store profile" in r.text)

# Test 11: Export CSV
r = s.get("http://127.0.0.1:5050/reports/export/inventory.csv")
test(11, f"Export CSV (status={r.status_code})", r.status_code == 200 and "SKU" in r.text)

# Test 12: Export PDF
r = s.get("http://127.0.0.1:5050/reports/export/sales.pdf")
test(12, f"Export PDF (status={r.status_code})", r.status_code == 200 and "application/pdf" in r.headers.get("content-type", ""))

# Test 13: Favicon
r = s.get("http://127.0.0.1:5050/static/favicon.svg")
test(13, f"Favicon SVG (status={r.status_code})", r.status_code == 200)

# Test 14: Logo
r = s.get("http://127.0.0.1:5050/static/logo.jpg")
test(14, f"Logo JPG (status={r.status_code})", r.status_code == 200)

# Test 15: Logo and Favicon in HTML
r = s.get("http://127.0.0.1:5050/dashboard")
test(15, "Logo in sidebar HTML", "logo.jpg" in r.text)
test(16, "Favicon in head HTML", "favicon.svg" in r.text)

# Test 17: Stock movement POST
r = s.get("http://127.0.0.1:5050/stock")
token_match = re.search(r'name="csrf_token".*?value="([^"]+)"', r.text)
if token_match:
    csrf = token_match.group(1)
    prod_match = re.search(r'<option value="(\d+)"', r.text)
    if prod_match:
        r = s.post("http://127.0.0.1:5050/stock", data={
            "csrf_token": csrf,
            "product_id": prod_match.group(1),
            "movement_type": "in",
            "quantity": "5",
            "note": "Test restock"
        }, allow_redirects=True)
        test(17, f"Stock movement POST (status={r.status_code})", r.status_code == 200 and "Stock movement recorded" in r.text)
    else:
        test(17, "Stock movement - product found", False)
else:
    test(17, "Stock movement - CSRF found", False)

# Test 18: Sale POST (Multi-product cart sale)
r = s.get("http://127.0.0.1:5050/sales")
token_match = re.search(r'name="csrf_token".*?value="([^"]+)"', r.text)
if token_match:
    csrf = token_match.group(1)
    prod_matches = re.findall(r'<option value="(\d+)"', r.text)
    if len(prod_matches) >= 2:
        r = s.post("http://127.0.0.1:5050/sales", data={
            "csrf_token": csrf,
            "product_id[]": [prod_matches[0], prod_matches[1]],
            "quantity[]": ["2", "3"]
        }, allow_redirects=True)
        test(18, f"Multi-product sale POST (status={r.status_code})", r.status_code == 200 and "completed successfully" in r.text)

        # Test 19: PDF Receipt download
        pdf_match = re.search(r'/sales/(\d+)/pdf', r.text)
        if pdf_match:
            pdf_url = f"http://127.0.0.1:5050/sales/{pdf_match.group(1)}/pdf"
            r_pdf = s.get(pdf_url)
            test(19, f"Sale PDF Receipt download (status={r_pdf.status_code})", r_pdf.status_code == 200 and r_pdf.headers.get("content-type") == "application/pdf")
        else:
            test(19, "Sale PDF Receipt link found", False)
    else:
        test(18, "Sale - products found", False)
else:
    test(18, "Sale - CSRF found", False)

# Test 20: Register page
s2 = requests.Session()
r = s2.get("http://127.0.0.1:5050/auth/register")
test(20, f"Register page (status={r.status_code})", r.status_code == 200 and "Create your account" in r.text)

print(f"\n{'='*40}")
print(f"Results: {ok} passed, {fail} failed out of {ok+fail} tests")
if fail:
    sys.exit(1)
