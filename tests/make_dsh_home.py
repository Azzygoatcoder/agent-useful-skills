"""Fixture for the DSH deploy/self-heal check.

Creates a temp DSH_HOME/skills populated with symlinks (POSIX) or junctions
(Windows) back into the repo's default skill set, so `redeploy-skills.ps1 -Check`
has a healthy deployment to validate on a fresh machine.

Usage: python tests/make_dsh_home.py <dsh_home>
Prints the skills/ path it created.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: make_dsh_home.py <dsh_home>", file=sys.stderr)
        return 2
    dsh_home = pathlib.Path(sys.argv[1])
    skills_dir = dsh_home / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    names = json.loads((ROOT / "skills.manifest.json").read_text(encoding="utf-8"))["default"]
    bases = [ROOT / "skills"] + [p / "skills" for p in sorted((ROOT / "plugins").iterdir())
                                 if (p / "skills").is_dir()]
    found: dict[str, pathlib.Path] = {}
    for base in bases:
        for sub in sorted(base.iterdir()):
            if sub.is_dir() and sub.name in names:
                found[sub.name] = sub

    created = 0
    for name in names:
        src = found.get(name)
        if src is None:
            print(f"WARNING: no source dir for '{name}'", file=sys.stderr)
            continue
        dest = skills_dir / name
        if dest.exists() or dest.is_symlink():
            continue
        if os.name == "nt":
            # directory junction needs no admin rights; mklink fallback via cmd
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(dest), str(src)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"WARNING: junction failed for {name}: {r.stdout}{r.stderr}",
                      file=sys.stderr)
                continue
        else:
            dest.symlink_to(src, target_is_directory=True)
        created += 1

    print(f"{skills_dir}")
    print(f"linked {created}/{len(names)} skills into {skills_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
