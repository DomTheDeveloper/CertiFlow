CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  region TEXT NOT NULL
);
CREATE TABLE orders (
  order_id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);
