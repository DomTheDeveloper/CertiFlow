import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from certiflow.bench.jaffle import FILES,PINNED_COMMIT,git_blob_sha

def test_pinned_jaffle_manifest_and_git_blob_hash():
    assert len(FILES)==13;assert len(PINNED_COMMIT)==40;assert git_blob_sha(b'hello\n')=='ce013625030ba8dba906f756967f9e9ca394464a'
