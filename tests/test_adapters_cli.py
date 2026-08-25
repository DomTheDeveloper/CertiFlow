import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from certiflow.adapters.catalog import CatalogAdapter
from certiflow.adapters.dbt import DbtManifestAdapter
from certiflow.graph import PipelineGraph

def test_catalog_adapter():
    rows=[{"relation":"users","column":"id","type":"int","ordinal":1,"primary_key":True},{"relation":"users","column":"email","type":"text","ordinal":2,"primary_key":False}]
    adapter=CatalogAdapter(rows,engine="postgres");nodes=list(adapter.nodes());facts=list(adapter.seed_facts());assert nodes[0].args["schema"]["id"]=="int";assert facts[0].kind=="Key"

def test_dbt_manifest_adapter():
    manifest={"nodes":{"model.x.base":{"resource_type":"model","depends_on":{"nodes":[]},"columns":{"id":{"data_type":"int"}}},"model.x.child":{"resource_type":"model","depends_on":{"nodes":["model.x.base"]},"columns":{"id":{"data_type":"int"}}}}}
    graph=PipelineGraph.from_nodes(DbtManifestAdapter(manifest).nodes());assert graph.topological_order()==["model.x.base","model.x.child"]

def test_cli_benchmark_runs():
    env=dict(os.environ);env["PYTHONPATH"]=str(ROOT/"src");proc=subprocess.run([sys.executable,"-m","certiflow.cli","benchmark","--nodes","50"],env=env,capture_output=True,text=True,check=True);assert json.loads(proc.stdout)["nodes"]==50

def test_cli_normalize_sql():
    env=dict(os.environ);env["PYTHONPATH"]=str(ROOT/"src");p=subprocess.run([sys.executable,"-m","certiflow.cli","normalize-sql","--sql","SELECT id FROM users","--name","q"],env=env,capture_output=True,text=True,check=True);rows=json.loads(p.stdout);assert [r["op"] for r in rows]==["Scan","Project"]
