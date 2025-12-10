# Inventory Management System (Flask + MongoDB)

A web-based **Inventory Management System** built using **Python (Flask)** and **MongoDB**. The system helps organizations keep track of products, suppliers, warehouses, stock levels, purchase orders, and sales orders from a single dashboard.

This project is suitable as an **academic DBMS mini project / major project** and is also a good reference for learning Flask + MongoDB.

---

## 1. Problem Statement

Many small and medium businesses still manage inventory in Excel sheets or on paper. This leads to:

- **No real-time stock visibility** across warehouses.
- **Manual errors** in calculating stock balances.
- **Difficulty in tracking purchases and sales** for each product.
- **No automatic alerts** when items reach a low stock level.

This project solves the above by providing a small but complete **web-based DBMS application** for inventory tracking.

---

## 2. Objectives

- **Centralize inventory data** (products, suppliers, warehouses, stock levels).
- **Maintain accurate stock** through purchase (inward) and sales (outward) transactions.
- **Prevent negative stock** using server-side validation.
- **Provide simple analytical views** (dashboard cards and charts).
- **Demonstrate DBMS concepts**: collections, relations, aggregation, lookups, and basic transaction-like operations.

---

## 3. Core Features

- **Authentication**
  - Login / logout with Flask session management.
  - Default admin user: `admin` / `admin123` (auto-created on first run).

- **Dashboard**
  - Summary cards for: total products, suppliers, warehouses, low stock items.
  - Bar chart: **Inventory by Category** using Chart.js.
  - Quick navigation shortcuts to main modules.

- **Product Management**
  - Add and list products.
  - Fields: SKU, name, category, unit price, reorder level.
  - Validation for mandatory fields and data types.
  - Enforces **unique SKU** for every product.

- **Supplier Management**
  - Add and list suppliers.
  - Details: name, contact person, phone, email.

- **Warehouse Management**
  - Add and list warehouses.
  - Details: name, location, code.
  - Enforces **unique warehouse code**.

- **Stock Management**
  - Maintains a `stock_levels` collection per **(product, warehouse)** combination.
  - Uses MongoDB `$lookup` to display stock with product and warehouse names.

- **Purchase Orders (Inward / Receive Stock)**
  - Record new purchases.
  - Fields: supplier, product, warehouse, quantity.
  - On save: **increases stock** in `stock_levels` for that product and warehouse.

- **Sales Orders (Outward / Dispatch Stock)**
  - Record sales/dispatches.
  - Fields: product, warehouse, quantity, customer name.
  - Checks available stock and **prevents negative stock**.
  - On save: **decreases stock** in `stock_levels`.

- **Reports**
  - **Low Stock Report**: lists products where total stock < reorder level.
  - Dashboard chart for inventory distribution by category.

---

## 4. Technology Stack

- **Backend:** Python 3, Flask
- **Database:** MongoDB (local or MongoDB Atlas) accessed via `pymongo`
- **Templating & UI:** Jinja2, Bootstrap 5, Bootstrap Icons, Chart.js
- **Environment:** `virtualenv`, `.env` + `python-dotenv`

---

## 5. Database Design (MongoDB Collections)

The application uses the following collections:

- **`users`**
  - Stores application users.
  - Fields (simplified): `_id`, `username`, `password_hash`, `role`.

- **`products`**
  - Fields: `_id`, `sku`, `name`, `category`, `unit_price`, `reorder_level`.

- **`suppliers`**
  - Fields: `_id`, `name`, `contact_person`, `phone`, `email`.

- **`warehouses`**
  - Fields: `_id`, `name`, `location`, `code`.

- **`stock_levels`**
  - Represents current on-hand quantity per product and warehouse.
  - Fields: `_id`, `product_id`, `warehouse_id`, `quantity`.

- **`purchase_orders`**
  - Records incoming stock.
  - Fields: `_id`, `supplier_id`, `product_id`, `warehouse_id`, `quantity`, `status`.

- **`sales_orders`**
  - Records outgoing stock.
  - Fields: `_id`, `product_id`, `warehouse_id`, `quantity`, `customer_name`, `status`.

**Key DBMS Concepts Used:**

- Use of **ObjectId** references between collections.
- Use of **aggregation** and `$group` to compute total quantities.
- Use of **`$lookup`** to join collections for reporting (stock view, dashboard).

---

## 6. Project Structure (Key Files)

- **`app.py`**
  - Main Flask application factory.
  - MongoDB connection and configuration using environment variables.
  - All routes for login, dashboard, products, suppliers, warehouses, stock, purchase orders, sales orders, and reports.

- **`templates/`**
  - `base.html` – shared layout, navigation bar, and Bootstrap assets.
  - `login.html` – login screen.
  - `dashboard.html` – summary cards and Chart.js bar chart.
  - `products.html`, `add_product.html` – product listing and form.
  - `suppliers.html`, `add_supplier.html` – supplier listing and form.
  - `warehouses.html`, `add_warehouse.html` – warehouse listing and form.
  - `stock.html` – stock levels per product and warehouse.
  - `purchase_orders.html` – form + list of purchase orders.
  - `sales_orders.html` – form + list of sales orders.
  - `low_stock.html` – low stock report.

- **`requirements.txt`** – Python dependencies.
- **`.env.example`** – example environment configuration file.

> Note: Template file names may differ slightly based on your local copy, but the overall module structure remains the same.

---

## 7. Setup & Installation

### 7.1. Clone / Copy the Project

Place the project in a folder, for example:

```text
d:\projects\dbms_inventory_management
```

### 7.2. Create and Activate Virtual Environment (Windows PowerShell)

```powershell
cd d:\projects\dbms_inventory_management
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 7.3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 7.4. Configure Environment Variables (`.env`)

Create a `.env` file in the project root (or copy `.env.example` to `.env`) and set:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGO_DB_NAME=inventory_management
SECRET_KEY=your-secret-key-here
```

- `MONGO_URI` can point to **MongoDB Atlas** or a local instance (`mongodb://localhost:27017`).
- `MONGO_DB_NAME` is the logical database name.
- `SECRET_KEY` is used by Flask for sessions.

### 7.5. Run the Application

```powershell
python app.py
```

Open the browser at:

```text
http://127.0.0.1:5000/
```

Login using the default credentials:

- **Username:** `admin`
- **Password:** `admin123`

The default admin user is automatically created if it does not exist.

---

## 8. Application Workflow (For Demo / Viva)

You can use this typical flow while demonstrating the project:

1. **Login**
   - Open the login page and sign in as `admin`.

2. **Create Master Data**
   - **Products**: Create a few products with category, unit price, and reorder level.
   - **Suppliers**: Add 1–2 suppliers.
   - **Warehouses**: Add at least one warehouse.

3. **Receive Stock (Purchase Orders)**
   - Go to **Purchase Orders**.
   - Select a supplier, product, warehouse, and enter quantity.
   - Submit and explain that this **increases stock** in `stock_levels`.

4. **View Stock**
   - Open the **Stock** page.
   - Show how the stock is shown per product and warehouse.

5. **Dispatch Stock (Sales Orders)**
   - Go to **Sales Orders**.
   - Select product, warehouse, enter quantity and customer name.
   - If you enter more than available quantity, the system shows an error and **prevents negative stock**.
   - Otherwise, stock is reduced.

6. **View Reports & Dashboard**
   - Go back to **Dashboard**: explain the summary cards and category chart.
   - Open **Low Stock Report** to show items where current stock is below the reorder level.

---

## 9. How This Demonstrates DBMS Concepts

- **Data modeling:** Separate collections for products, suppliers, warehouses, stock, and orders.
- **Relationships:** References between documents using `ObjectId` (similar to foreign keys).
- **Aggregation:** `$group` pipeline stages to compute total available stock.
- **Joins:** `$lookup` to join `stock_levels` with `products` and `warehouses`.
- **Constraints at application level:** Unique SKU, unique warehouse code, and non-negative stock check.

You can highlight these points during viva / project evaluation.

---

## 10. Future Enhancements

- Role-based access control (admin, inventory manager, sales, viewer).
- Product search, filtering, and category management page.
- Export of reports to CSV/PDF.
- Email / SMS notifications for low stock.
- Barcode/QR integration for faster stock operations.
- Deployment to a cloud platform with MongoDB Atlas.

---

## 11. License / Usage

This project is developed as an **academic DBMS project**. You may reuse and adapt the code for **learning**, **assignments**, and **personal projects**. For any academic submission, you should add your own customizations and properly reference the source.

