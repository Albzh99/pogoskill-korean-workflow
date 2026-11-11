"""Release guard; emits file/line/category only, never matched values."""
import json, re, sys
from pathlib import Path
from manifest import ROOT, FILES, inventory
PATTERNS={
 "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
 "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
 "github_token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})"),
 "google_refresh_token":re.compile(r"1//[A-Za-z0-9_-]{30,}"),
 "credential_literal":re.compile(r"(?i)(?:api[_-]?key|access_token|refresh_token|client_secret|developer_token|password)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_./+\-=]{16,}[\"']"),
 "machine_path":re.compile(r"(?i)(?:[CD]:[/\\](?:Users|user)[/\\]|/Users/[^/]+/|/home/[^/]+/)"),
 "cms_write_route":re.compile(r"(?i)/cms/[^\s\"']*(?:save|update|delete|publish|upload|make)"),
}
def scan(text):
 return [{"line":text.count("\n",0,m.start())+1,"category":name} for name,pattern in PATTERNS.items() for m in pattern.finditer(text)]
def main():
 inventory() # Unexpected filenames and absent allowlisted files are failures too.
 findings=[]
 for name in FILES:
  if name=="scripts/secret_scan.py":continue # Patterns are intentional detection signatures.
  text=(ROOT/name).read_text(encoding="utf-8")
  findings.extend({"file":name,**item} for item in scan(text))
 print(json.dumps({"passed":not findings,"files_checked":len(FILES)-1,"findings":findings,"note":"Heuristic guard, not proof that no secret exists. Review whitelist and diff."}))
 return bool(findings)
if __name__=="__main__":sys.exit(main())
