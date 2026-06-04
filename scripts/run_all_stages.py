"""Run the public staged BS0832 reproduction chain from v106 through v109."""
from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from app.domain.stage_v106 import run_stage_v106
from app.domain.stage_v107 import run_stage_v107
from app.domain.stage_v108 import run_stage_v108
from app.domain.stage_v109 import run_stage_v109
from app.domain.io_utils import write_json
from ._logging import configure_logging


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the staged reproduction chain."""
    parser = argparse.ArgumentParser(description="Replay the public BS0832 staged certificate chain.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root; defaults to current directory.")
    parser.add_argument("--prefix", default="stage", help="Prefix for run identifiers under runs/.")
    parser.add_argument("--log-level", default="INFO", help="Loguru log level.")
    return parser.parse_args()


def main() -> int:
    """Run v106, v107, v108, and v109 in sequence."""
    args = parse_args()
    root = args.root.resolve()
    configure_logging(root / "runs" / f"{args.prefix}_all" / "public_stage_chain.log", args.log_level)
    try:
        logger.info("Starting full staged BS0832 chain")
        r106 = run_stage_v106(root=root, run_id=f"{args.prefix}_v106", log_level=args.log_level)
        v106_zip = Path(r106["generated_feedback_zip"])
        r107 = run_stage_v107(root=root, v106_feedback_zip=v106_zip, run_id=f"{args.prefix}_v107", log_level=args.log_level)
        v107_zip = Path(r107["generated_feedback_zip"])
        r108 = run_stage_v108(
            root=root,
            v107_feedback_zip=v107_zip,
            v106_feedback_zip=v106_zip,
            run_id=f"{args.prefix}_v108",
            log_level=args.log_level,
        )
        # The bundled author signoff is SHA-bound to the reference v108 archive
        # stored under certificate/intermediate/.  The all-stage command validates
        # that signed reference archive and also runs a generated-chain v109 check
        # on the freshly generated v108 archive without applying the bundled signoff.
        r109_reference = run_stage_v109(
            root=root,
            signoff_json=root / "certificate" / "reviewer_signoff_v109.json",
            run_id=f"{args.prefix}_v109_reference",
            log_level=args.log_level,
            mode="reference-signed",
        )
        v108_zip = Path(r108["generated_feedback_zip"])
        r109_generated = run_stage_v109(
            root=root,
            v108_feedback_zip=v108_zip,
            signoff_json=None,
            run_id=f"{args.prefix}_v109_generated",
            log_level=args.log_level,
            mode="generated-chain",
        )
        chain_summary = {
            "status": "success",
            "purpose": "Run the public staged BS0832 certificate chain.",
            "v106": r106,
            "v107": r107,
            "v108": r108,
            "v109_reference_signed": r109_reference,
            "v109_generated_chain": r109_generated,
            "note": (
                "The reference-signed v109 run validates the bundled author signoff against the "
                "reference v108 archive. The generated-chain path threads the freshly generated "
                "v106 archive into v107 and v108 before replaying v109 on the freshly generated "
                "v108 archive. It does not assume that the reference signoff applies to the new "
                "outer ZIP file."
            ),
        }
        write_json(root / "runs" / f"{args.prefix}_all" / "stage_chain_summary.json", chain_summary)
        logger.success("Full staged BS0832 chain completed")
        return 0
    except Exception:
        logger.exception("Full staged BS0832 chain failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
