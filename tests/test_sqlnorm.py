import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.sqlnorm import normalize_select,SQLNormalizationError

def test_select_join_filter_project_normalization():
    nodes=normalize_select("SELECT o.order_id AS id, c.region FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id WHERE o.amount > 10",name="q");assert [n.op for n in nodes]==["Scan","Scan","Join","Filter","Project"];assert nodes[2].args["equi"]==(("customer_id","customer_id"),);assert nodes[-1].args["mapping"]=={"id":"order_id","region":"region"}

def test_group_normalization():
    nodes=normalize_select("SELECT region, sum(amount) AS revenue FROM sales GROUP BY region",name="agg");assert [n.op for n in nodes]==["Scan","Group"];assert nodes[-1].args["group_by"]==("region",);assert "revenue" in nodes[-1].args["aggregates"]

def test_unsupported_sql_rejected():
    for sql in ["DELETE FROM t","SELECT id FROM t ORDER BY id","SELECT * FROM a JOIN b ON a.id=b.id AND a.x=b.x"]:
        try:normalize_select(sql);assert False,sql
        except SQLNormalizationError:pass
