"""Automated Database Seeding Script.

Populates sample e-commerce analytics data across:
- SQLite (local file: data/nl2db_sample.db)
- MongoDB (localhost:27017 / nl2db_test)
- MySQL (localhost:3306 / nl2db_test)
- PostgreSQL (localhost:5432 / nl2db_test)
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
import aiosqlite
from motor.motor_asyncio import AsyncIOMotorClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.app.config import get_settings


# Sample Data
CATEGORIES = [
    (1, "Electronics", "electronics"),
    (2, "Audio", "audio"),
    (3, "Home Appliances", "home-appliances"),
    (4, "Accessories", "accessories"),
]

CUSTOMERS = [
    (1, "Alice Morgan", "alice.morgan@example.com", "gold", "2024-01-15 10:30:00"),
    (2, "Bob Vance", "bob.vance@example.com", "silver", "2024-02-20 14:15:00"),
    (3, "Charlie Day", "charlie.day@example.com", "bronze", "2024-03-05 09:00:00"),
    (4, "Diana Prince", "diana.prince@example.com", "platinum", "2023-11-12 18:45:00"),
    (5, "Evan Wright", "evan.wright@example.com", "bronze", "2024-04-18 11:20:00"),
    (6, "Fiona Gallagher", "fiona.g@example.com", "gold", "2024-05-22 16:30:00"),
]

PRODUCTS = [
    (1, "Quantum Pro Laptop", 1, 1499.99, 45),
    (2, "UltraVision 4K Monitor", 1, 399.99, 80),
    (3, "SonicNoise ANC Headphones", 2, 249.99, 120),
    (4, "TrueBass Earbuds", 2, 89.99, 200),
    (5, "Smart Air Purifier Pro", 3, 199.99, 60),
    (6, "RoboVac 3000", 3, 349.99, 35),
    (7, "Ergonomic Mechanical Keyboard", 4, 129.99, 150),
    (8, "Precision Wireless Mouse", 4, 69.99, 210),
    (9, "USB-C Multiport Dock", 4, 59.99, 175),
]

ORDERS = [
    (1, 1, "2024-06-01 10:15:00", "delivered", 1749.98),
    (2, 2, "2024-06-05 14:20:00", "delivered", 339.98),
    (3, 4, "2024-06-10 09:45:00", "delivered", 2249.97),
    (4, 3, "2024-06-12 11:30:00", "processing", 89.99),
    (5, 1, "2024-06-18 16:00:00", "delivered", 199.99),
    (6, 6, "2024-06-20 13:10:00", "shipped", 479.98),
    (7, 5, "2024-06-22 17:50:00", "cancelled", 1499.99),
    (8, 4, "2024-06-25 15:05:00", "delivered", 189.98),
]

ORDER_ITEMS = [
    (1, 1, 1, 1, 1499.99),
    (2, 1, 3, 1, 249.99),
    (3, 2, 3, 1, 249.99),
    (4, 2, 4, 1, 89.99),
    (5, 3, 1, 1, 1499.99),
    (6, 3, 2, 1, 399.99),
    (7, 3, 3, 1, 249.99),
    (8, 3, 8, 1, 69.99),
    (9, 4, 4, 1, 89.99),
    (10, 5, 5, 1, 199.99),
    (11, 6, 6, 1, 349.99),
    (12, 6, 7, 1, 129.99),
    (13, 7, 1, 1, 1499.99),
    (14, 8, 7, 1, 129.99),
    (15, 8, 9, 1, 59.99),
]


SQL_DDL = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    tier VARCHAR(20) NOT NULL DEFAULT 'bronze',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category_id INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'processing',
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);
"""


async def seed_sqlite(db_path: str) -> None:
    print(f"\n[1/4] Seeding SQLite database ({db_path})...")
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SQL_DDL)
        await db.executemany("INSERT INTO categories VALUES (?, ?, ?);", CATEGORIES)
        await db.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?);", CUSTOMERS)
        await db.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?);", PRODUCTS)
        await db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?);", ORDERS)
        await db.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?);", ORDER_ITEMS)
        await db.commit()
    print(" SQLite seeded successfully.")


async def seed_mongodb(uri: str, db_name: str) -> None:
    print(f"\n[2/4] Seeding MongoDB ({uri} / {db_name})...")
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2500)
        db = client[db_name]
        await client.server_info()

        # Clean collections
        for col_name in ["customers", "categories", "products", "orders"]:
            await db[col_name].drop()

        # Insert categories
        cats_docs = [{"_id": c[0], "name": c[1], "slug": c[2]} for c in CATEGORIES]
        await db["categories"].insert_many(cats_docs)

        # Insert customers
        cust_docs = [
            {"_id": c[0], "name": c[1], "email": c[2], "tier": c[3], "created_at": c[4]}
            for c in CUSTOMERS
        ]
        await db["customers"].insert_many(cust_docs)

        # Insert products
        prod_docs = [
            {"_id": p[0], "name": p[1], "category_id": p[2], "price": p[3], "stock": p[4]}
            for p in PRODUCTS
        ]
        await db["products"].insert_many(prod_docs)

        # Insert orders (with embedded items)
        order_docs = []
        for o in ORDERS:
            items = [
                {"product_id": oi[2], "quantity": oi[3], "unit_price": oi[4]}
                for oi in ORDER_ITEMS if oi[1] == o[0]
            ]
            order_docs.append({
                "_id": o[0],
                "customer_id": o[1],
                "order_date": o[2],
                "status": o[3],
                "total_amount": o[4],
                "items": items
            })
        await db["orders"].insert_many(order_docs)
        print(" MongoDB seeded successfully.")
    except Exception as e:
        print(f" MongoDB seeding skipped: {e}")


async def seed_mysql(settings) -> None:
    print(f"\n[3/4] Seeding MySQL ({settings.MYSQL_HOST}:{settings.MYSQL_PORT})...")
    try:
        import aiomysql
        conn = await asyncio.wait_for(
            aiomysql.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
            ),
            timeout=3.0,
        )
        async with conn.cursor() as cur:
            await cur.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DATABASE}`;")
            await cur.execute(f"USE `{settings.MYSQL_DATABASE}`;")
            # Drop in order
            for tbl in ["order_items", "orders", "products", "categories", "customers"]:
                await cur.execute(f"DROP TABLE IF EXISTS `{tbl}`;")

            await cur.execute("""
            CREATE TABLE categories (
                id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(100) NOT NULL
            );
            """)
            await cur.execute("""
            CREATE TABLE customers (
                id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                tier VARCHAR(20) NOT NULL DEFAULT 'bronze',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await cur.execute("""
            CREATE TABLE products (
                id INT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                category_id INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                stock INT NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            );
            """)
            await cur.execute("""
            CREATE TABLE orders (
                id INT PRIMARY KEY,
                customer_id INT NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(30) NOT NULL DEFAULT 'processing',
                total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );
            """)
            await cur.execute("""
            CREATE TABLE order_items (
                id INT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                unit_price DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
            """)

            await cur.executemany("INSERT INTO categories VALUES (%s, %s, %s);", CATEGORIES)
            await cur.executemany("INSERT INTO customers VALUES (%s, %s, %s, %s, %s);", CUSTOMERS)
            await cur.executemany("INSERT INTO products VALUES (%s, %s, %s, %s, %s);", PRODUCTS)
            await cur.executemany("INSERT INTO orders VALUES (%s, %s, %s, %s, %s);", ORDERS)
            await cur.executemany("INSERT INTO order_items VALUES (%s, %s, %s, %s, %s);", ORDER_ITEMS)
            await conn.commit()
        conn.close()
        print(" MySQL seeded successfully.")
    except Exception as e:
        print(f" MySQL seeding skipped: {e}")


async def seed_postgres(settings) -> None:
    print(f"\n[4/4] Seeding PostgreSQL ({settings.POSTGRES_HOST}:{settings.POSTGRES_PORT})...")
    try:
        import asyncpg
        # Try connecting to postgres to create db if needed
        sys_conn = await asyncio.wait_for(
            asyncpg.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database="postgres",
            ),
            timeout=3.0,
        )
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", settings.POSTGRES_DATABASE
        )
        if not exists:
            await sys_conn.execute(f'CREATE DATABASE "{settings.POSTGRES_DATABASE}"')
        await sys_conn.close()

        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DATABASE,
        )

        for tbl in ["order_items", "orders", "products", "categories", "customers"]:
            await conn.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE;")

        await conn.execute("""
        CREATE TABLE categories (
            id INT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL
        );
        CREATE TABLE customers (
            id INT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            tier VARCHAR(20) NOT NULL DEFAULT 'bronze',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE products (
            id INT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            category_id INT NOT NULL REFERENCES categories (id),
            price NUMERIC(10, 2) NOT NULL,
            stock INT NOT NULL DEFAULT 0
        );
        CREATE TABLE orders (
            id INT PRIMARY KEY,
            customer_id INT NOT NULL REFERENCES customers (id),
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(30) NOT NULL DEFAULT 'processing',
            total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0
        );
        CREATE TABLE order_items (
            id INT PRIMARY KEY,
            order_id INT NOT NULL REFERENCES orders (id),
            product_id INT NOT NULL REFERENCES products (id),
            quantity INT NOT NULL DEFAULT 1,
            unit_price NUMERIC(10, 2) NOT NULL
        );
        """)

        await conn.executemany("INSERT INTO categories VALUES ($1, $2, $3);", CATEGORIES)
        parsed_customers = [
            (c[0], c[1], c[2], c[3], datetime.strptime(c[4], "%Y-%m-%d %H:%M:%S"))
            for c in CUSTOMERS
        ]
        await conn.executemany("INSERT INTO customers VALUES ($1, $2, $3, $4, $5);", parsed_customers)
        await conn.executemany("INSERT INTO products VALUES ($1, $2, $3, $4, $5);", PRODUCTS)
        parsed_orders = [
            (o[0], o[1], datetime.strptime(o[2], "%Y-%m-%d %H:%M:%S"), o[3], o[4])
            for o in ORDERS
        ]
        await conn.executemany("INSERT INTO orders VALUES ($1, $2, $3, $4, $5);", parsed_orders)
        await conn.executemany("INSERT INTO order_items VALUES ($1, $2, $3, $4, $5);", ORDER_ITEMS)
        await conn.close()
        print(" PostgreSQL seeded successfully.")
    except Exception as e:
        print(f" PostgreSQL seeding skipped: {e}")


async def main() -> None:
    settings = get_settings()
    print("=" * 60)
    print("NL2DB Local Database Seeder")
    print("=" * 60)
    await seed_sqlite(settings.SQLITE_DB_PATH)
    await seed_mongodb(settings.MONGODB_URI, settings.MONGODB_DATABASE)
    await seed_mysql(settings)
    await seed_postgres(settings)
    print("\n" + "=" * 60)
    print("Database seeding completed.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
