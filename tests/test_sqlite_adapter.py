import sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.adapters.sqlite import SQLiteAdapter

def test_live_sqlite_catalog_and_unique_keys(tmp_path):
    db=tmp_path/"demo.db";con=sqlite3.connect(db);con.executescript("CREATE TABLE customers(customer_id INTEGER PRIMARY KEY,email TEXT NOT NULL UNIQUE,region TEXT); CREATE TABLE orders(order_id INTEGER PRIMARY KEY,customer_id INTEGER NOT NULL,amount REAL);");con.commit();con.close();a=SQLiteAdapter.from_path(db);nodes={n.name:n for n in a.nodes()};facts=list(a.seed_facts());a.close();assert set(nodes)=={"customers","orders"};assert nodes["customers"].args["schema"]["customer_id"]=="integer";keys={(f.subject,tuple(dict(f.payload)["columns"])) for f in facts if f.kind=="Key"};assert ("customers",("customer_id",)) in keys;assert ("customers",("email",)) in keys;assert ("orders",("order_id",)) in keys
