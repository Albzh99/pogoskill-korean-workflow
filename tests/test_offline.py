import contextlib, importlib.util, io, json, sys, tempfile, unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
import connections as c
import secret_scan, manifest, workflow
class Offline(unittest.TestCase):
 def test_windows(self):
  values=c.windows("UTC", datetime(2026,11,11));self.assertEqual([(n,str(s),str(e)) for n,s,e in values],[("recent7","2026-11-04","2026-11-10"),("previous7","2026-10-28","2026-11-03"),("recent28","2026-10-14","2026-11-10")])
 def test_doctor_missing_all_dependencies(self):
  with patch.object(c.importlib.util,"find_spec",side_effect=ModuleNotFoundError):
   result=c.doctor()
  self.assertFalse(any(result["dependencies"].values()));self.assertFalse(result["network_performed"])
 def test_ads_requires_reason_before_import(self):
  with self.assertRaises(c.SafeError):c.ads(["한국어"],"valid_low_volume")
 def test_missing_keyword_rejected(self):
  with patch.object(sys,"argv",["connections.py","query","semrush","--out","work/a.json"]),patch.object(c,"semrush",side_effect=AssertionError("network forbidden")),contextlib.redirect_stdout(io.StringIO()) as out:
   self.assertEqual(c.main(),1)
  self.assertIn("keywords_required",out.getvalue())
 def test_private_output_required(self):
  with patch.object(sys,"argv",["connections.py","query","ga4","--out","README.md"]),contextlib.redirect_stdout(io.StringIO()) as out:
   self.assertEqual(c.main(),1)
  self.assertIn("output_must_be_private",out.getvalue())
 def test_external_runtime_error_never_echoed(self):
  sensitive="doNotPrintThisCredentialValue"
  with patch.object(sys,"argv",["connections.py","doctor"]),patch.object(c,"doctor",side_effect=RuntimeError(sensitive)),contextlib.redirect_stdout(io.StringIO()) as out:
   self.assertEqual(c.main(),1)
  self.assertNotIn(sensitive,out.getvalue());self.assertIn("connection_or_environment_failure",out.getvalue())
 def test_scan_never_returns_secret_value(self):
  fake="ghp_"+"a"*36;result=secret_scan.scan(fake)
  self.assertTrue(result);self.assertNotIn(fake,json.dumps(result))
 def test_literal_scan(self):
  fake='api_key = "'+"a"*24+'"';self.assertTrue(secret_scan.scan(fake))
 def test_whitelist_has_no_cms_scripts(self):
  self.assertFalse(any("cms" in p.lower() for p in manifest.FILES));self.assertEqual(len(manifest.FILES),len(set(manifest.FILES)))
 def test_manifest_inventory(self):self.assertEqual(len(manifest.inventory()),len(manifest.FILES))
 def test_two_round_gate(self):
  data={k:[] for k in workflow.FIELDS};data["validation"]={k:{"path":"work/a","sha256":"x"} for k in ("selected_source","word","seo","hero","body_images","guide_evidence","fact_evidence","mechanical_report","visual_report")}
  with patch.object(workflow,"handoff",return_value=data),patch.object(workflow,"ref"):
   with self.assertRaisesRegex(ValueError,"two_actual"):workflow.delivery(ROOT/"work/handoff.json")
 def test_changed_seo_invalidates_review(self):
  names=("selected_source","word","seo","hero","body_images","guide_evidence","fact_evidence","mechanical_report","visual_report")
  refs={k:{"path":"work/"+k,"sha256":"old"} for k in names}
  agents={s:s+"-agent" for s in ("source","ga4","search","translate","review")}
  rounds=[{"round":i,"reviewer_id":agents["review"],"report":{"path":"work/report","sha256":"old"},"responses":{"path":"work/responses","sha256":"old"},"status":"passed","manuscript_sha256":"old","input_bindings":dict(refs)} for i in (1,2)]
  data={k:[] for k in workflow.FIELDS};data["validation"]={**refs,"review_rounds":rounds,"stage_agent_ids":agents}
  with patch.object(workflow,"handoff",return_value=data),patch.object(workflow,"ref"):
   self.assertTrue(workflow.delivery(ROOT/"work/handoff.json")["local_delivery_file_gate_passed"])
   data["validation"]["seo"]={"path":"work/seo","sha256":"changed"}
   with self.assertRaisesRegex(ValueError,"binding_mismatch_seo"):workflow.delivery(ROOT/"work/handoff.json")
if __name__=="__main__":unittest.main()
