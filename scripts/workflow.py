"""Local version-bound handoff checks; cannot verify semantic quality or independence."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDS={"goal","completed","decisions","artifacts","validation","unresolved","next_context"}
def load(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def ref(value):
 p=(ROOT/value["path"]).resolve()
 if not p.is_relative_to(ROOT/"work") and not p.is_relative_to(ROOT/".local"):raise ValueError("article_artifact_must_be_private")
 if hashlib.sha256(p.read_bytes()).hexdigest()!=value["sha256"]:raise ValueError("artifact_hash_mismatch")
def handoff(path):
 data=load(path)
 if not FIELDS.issubset(data):raise ValueError("seven_handoff_fields_required")
 for item in data["artifacts"]:ref(item)
 return data
def delivery(path):
 data=handoff(path);v=data["validation"]
 if data["unresolved"]:raise ValueError("unresolved_items_block_delivery")
 bound_fields=("selected_source","word","seo","hero","body_images","guide_evidence","fact_evidence","mechanical_report","visual_report")
 for name in bound_fields:
  if not v.get(name):raise ValueError("missing_evidence_"+name)
  refs=v[name] if isinstance(v[name],list) else [v[name]]
  for value in refs:ref(value)
 rounds=v.get("review_rounds",[])
 if len(rounds)<2:raise ValueError("two_actual_review_rounds_required")
 reviewer=rounds[0].get("reviewer_id")
 if not reviewer:raise ValueError("actual_reviewer_id_required")
 agents=v.get("stage_agent_ids",{})
 expected={"source","ga4","search","translate","review"}
 if not expected.issubset(agents) or any(not agents[s] for s in expected):raise ValueError("actual_stage_agent_ids_required")
 if len({agents[s] for s in expected})!=len(expected) or agents["review"]!=reviewer:raise ValueError("roles_must_be_independent")
 for index,rd in enumerate(rounds,1):
  if rd.get("reviewer_id")!=reviewer:raise ValueError("same_reviewer_required")
  if rd.get("round")!=index:raise ValueError("review_sequence_required")
  ref(rd["report"])
  if index>1:ref(rd["responses"])
 final=rounds[-1]
 if final.get("status")!="passed" or final.get("manuscript_sha256")!=v["word"]["sha256"]:raise ValueError("final_review_must_bind_final_word")
 bindings=final.get("input_bindings",{})
 for name in bound_fields:
  if bindings.get(name)!=v[name]:raise ValueError("final_review_binding_mismatch_"+name)
 return {"local_delivery_file_gate_passed":True,"warning":"Declared evidence and IDs still require real independent agent and content verification."}
def main():
 a=argparse.ArgumentParser();a.add_argument("mode",choices=["handoff","delivery"]);a.add_argument("path");args=a.parse_args();p=(ROOT/args.path).resolve()
 if not p.is_relative_to(ROOT):raise ValueError("path_outside_workspace")
 result=delivery(p) if args.mode=="delivery" else {"handoff_file_gate_passed":bool(handoff(p))};print(json.dumps(result))
if __name__=="__main__":main()
