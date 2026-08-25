from __future__ import annotations
"""Pinned real-corpus evaluation over dbt Labs' Jaffle Shop project."""
from hashlib import sha1
import json
from pathlib import Path
import tempfile
from urllib.request import Request,urlopen
from .dbt_corpus import evaluate_dbt_directory

PINNED_COMMIT="7d0d8de2d58edae06f0724a3892da0224bbf0f4a"
BASE=f"https://raw.githubusercontent.com/dbt-labs/jaffle-shop/{PINNED_COMMIT}/"
FILES={
"models/marts/customers.sql":"129eb8ffc6937e4d8c11320ab509d3777789fb3b",
"models/marts/locations.sql":"31bbd08ddc27160e5f439a7c843d4089f9b7eb3b",
"models/marts/metricflow_time_spine.sql":"bebc9e61d68f7ac7a23aeb4b9a95349de179995f",
"models/marts/order_items.sql":"5b7534f083c44f49416a555561773404547809dd",
"models/marts/orders.sql":"56fdc5912a88222f17de84fca82d0845cfb55f43",
"models/marts/products.sql":"f276d292f6a2007b72bcf0e86ad29005e8f57a9d",
"models/marts/supplies.sql":"820cb8c52f9519ed5d4cb2dea5e4fea42f80acfd",
"models/staging/stg_customers.sql":"2b928df37c4a84fd0d0e0fe639b76d1ce90007c5",
"models/staging/stg_locations.sql":"551e1ba2b632dc8e4f9620488015df820cc5abfb",
"models/staging/stg_order_items.sql":"5459a84b0b8561550c2d39be159519c3b78ef82d",
"models/staging/stg_orders.sql":"61408c082bf7ea43d542aff34c24e57aaa4075f7",
"models/staging/stg_products.sql":"0299eed610551b7c0d0fff997684d99feb0819ff",
"models/staging/stg_supplies.sql":"0f665133b290df90f0f516832d6a09befbbd0e5e"}

def git_blob_sha(data:bytes)->str:return sha1(f"blob {len(data)}\0".encode("ascii")+data).hexdigest()
def fetch_pinned_corpus(destination:str|Path)->Path:
    root=Path(destination)
    for path,expected_sha in FILES.items():
        req=Request(BASE+path,headers={"User-Agent":"CertiFlow-reproducibility-artifact"})
        with urlopen(req,timeout=30) as response:data=response.read()
        actual=git_blob_sha(data)
        if actual!=expected_sha:raise RuntimeError(f"blob hash mismatch for {path}: expected {expected_sha}, got {actual}")
        target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return root/"models"
def run_jaffle_evaluation(destination:str|Path|None=None)->dict:
    if destination is None:
        with tempfile.TemporaryDirectory(prefix="certiflow-jaffle-") as tmp:result=evaluate_dbt_directory(fetch_pinned_corpus(tmp)).as_dict()
    else:result=evaluate_dbt_directory(fetch_pinned_corpus(destination)).as_dict()
    return {"repository":"dbt-labs/jaffle-shop","commit":PINNED_COMMIT,"verified_files":len(FILES),**result}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--destination",default=None);args=p.parse_args();print(json.dumps(run_jaffle_evaluation(args.destination),indent=2,sort_keys=True))
