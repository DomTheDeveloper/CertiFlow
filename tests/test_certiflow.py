from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from certiflow import Certificate, IRNode, Verdict, example_pipeline


def run() -> None:
    nodes, store, checker = example_pipeline()
    join, group = nodes

    join_cert = Certificate(
        subject_hash=join.hash,
        rule="join_fanout",
        assumptions=(),
        claims=(),
        witness={
            "left_col": "customer_id",
            "right_col": "customer_id",
            "right_relation": "customers",
        },
    )
    r1 = checker.verify(join, join_cert)
    assert r1.verdict == Verdict.ACCEPT

    grain_cert = Certificate(
        subject_hash=group.hash,
        rule="group_grain",
        assumptions=(r1.claims[0].id,),
        claims=(),
        witness={"grain": ("region",)},
    )
    r2 = checker.verify(group, grain_cert)
    assert r2.verdict == Verdict.ACCEPT

    bad_join = IRNode(
        op="Join",
        name="bad_join",
        args={"join_type": "left", "equi": (("customer_id", "region"),)},
        inputs=("orders", "customers"),
    )
    bad_cert = Certificate(
        subject_hash=bad_join.hash,
        rule="join_fanout",
        assumptions=(),
        claims=(),
        witness={
            "left_col": "customer_id",
            "right_col": "region",
            "right_relation": "customers",
        },
    )
    r3 = checker.verify(bad_join, bad_cert)
    assert r3.verdict == Verdict.UNKNOWN

    stale_cert = Certificate(
        subject_hash="0" * 64,
        rule="join_fanout",
        assumptions=(),
        claims=(),
        witness={},
    )
    r4 = checker.verify(join, stale_cert)
    assert r4.verdict == Verdict.REJECT

    print("CertiFlow reference prototype: 4/4 core checks passed")


if __name__ == "__main__":
    run()
