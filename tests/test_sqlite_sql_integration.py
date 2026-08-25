import sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.adapters.sqlite import SQLiteAdapter
from certiflow.sqlnorm import normalize_select
from certiflow.graph import PipelineGraph
from certiflow.engine import VerificationEngine

def test_live_sqlite_metadata_feeds_join_certificate():
    con=sqlite3.connect(':memory:');con.executescript('CREATE TABLE customers(customer_id INTEGER PRIMARY KEY, region TEXT); CREATE TABLE orders(order_id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL);');adapter=SQLiteAdapter(con,source='memory');facts=list(adapter.seed_facts());nodes=normalize_select('SELECT o.order_id, c.region FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id WHERE o.amount > 10',name='report',engine='sqlite');report=VerificationEngine().verify(PipelineGraph.from_nodes(nodes),facts);join_results=[r for name,r in report.results if 'join' in name and r.rule=='join_fanout'];assert len(join_results)==1 and join_results[0].accepted
