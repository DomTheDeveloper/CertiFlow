import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).parents[1]; sys.path.insert(0,str(ROOT/"src"))
from certiflow.adapters.catalog import CatalogAdapter
from certiflow.adapters.dbt import DbtManifestAdapter
from certiflow.graph import PipelineGraph

def test_catalog_adapter():
    a=CatalogAdapter([{"relation":"users","column":"id","type":"int","ordinal":1,"primary_key":True},{"relation":"users","column":"email","type":"text","ordinal":2,"primary_key":False}],engine="postgres"); assert list(a.nodes())[0].args["schema"]["id"]=="int"; assert list(a.seed_facts())[0].kind=="Key"
def test_dbt_adapter():
    m={"nodes":{"model.x.base":{"resource_type":"model","depends_on":{"nodes":[]},"columns":{"id":{"data_type":"int"}}},"model.x.child":{"resource_type":"model","depends_on":{"nodes":["model.x.base"]},"columns":{"id":{"data_type":"int"}}}}}; assert PipelineGraph.from_nodes(DbtManifestAdapter(m).nodes()).topological_order()==["model.x.base","model.x.child"]
def test_cli_benchmark():
    env=dict(os.environ); env["PYTHONPATH"]=str(ROOT/"src"); p=subprocess.run([sys.executable,"-m","certiflow.cli","benchmark","--nodes","50"],env=env,capture_output=True,text=True,check=True); assert json.loads(p.stdout)["nodes"]==50
