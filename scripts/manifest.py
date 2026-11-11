"""Explicit release whitelist and SHA256 inventory. No private data discovery."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAGES=("source","ga4","search","translate","review","operations")
FILES=(".gitattributes","AGENTS.md","README.md",".gitignore","requirements.txt","config.example.json","knowledge/policy.json","knowledge/article-pipeline.md","knowledge/connections.md","knowledge/portable-contract.md","knowledge/document-media.md","scripts/connections.py","scripts/manifest.py","scripts/secret_scan.py","scripts/workflow.py","tests/test_offline.py") + tuple("knowledge/stages/"+s+".md" for s in STAGES) + tuple(".agents/skills/pogoskill-kr-"+s+"/SKILL.md" for s in STAGES+("pipeline",))
IGNORED={".git",".local","work",".venv","__pycache__"}
def inventory():
    missing=[p for p in FILES if not (ROOT/p).is_file()]
    extras=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and not any(x in IGNORED for x in p.relative_to(ROOT).parts) and p.relative_to(ROOT).as_posix() not in (*FILES,"manifest.json")]
    if missing or extras: raise ValueError("release_file_set_mismatch: "+json.dumps({"missing":missing,"unexpected":extras}))
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(FILES)}
def main():
    a=argparse.ArgumentParser();a.add_argument("--check",action="store_true");args=a.parse_args();actual={"schema":"explicit-whitelist-sha256-v1","files":inventory()};path=ROOT/"manifest.json"
    if args.check:
        if not path.exists() or json.loads(path.read_text(encoding="utf-8"))!=actual: raise ValueError("manifest_mismatch")
        print(json.dumps({"manifest_verified":True,"files":len(FILES)}))
    else:
        path.write_text(json.dumps(actual,indent=2)+"\n",encoding="utf-8");print(json.dumps({"manifest_written":True,"files":len(FILES)}))
if __name__=="__main__":main()
