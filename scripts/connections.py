"""Read-only portable connectors. Never print credentials or raw exceptions."""
import argparse, csv, getpass, importlib.util, io, json, os, shutil, sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo
class SafeError(Exception):
    """Only fixed internal codes may be shown; external exception strings stay private."""

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
SCOPES = {"ga4": ["https://www.googleapis.com/auth/analytics.readonly"], "ads": ["https://www.googleapis.com/auth/adwords"]}
SERVICE = "pogoskill-korean-workflow"

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try: path.chmod(0o600)
    except OSError: pass

def config():
    path = LOCAL / "config.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

def vault():
    import keyring
    # Fail closed when no secure backend is installed. No plaintext fallback.
    backend = keyring.get_keyring()
    allowed = ("keyring.backends.Windows", "keyring.backends.macOS", "keyring.backends.SecretService", "keyring.backends.libsecret", "keyring.backends.kwallet")
    candidates = getattr(backend, "backends", [backend])
    for candidate in candidates:
        if type(candidate).__module__.startswith(allowed) and candidate.priority > 0:
            keyring.set_keyring(candidate)
            return keyring
    raise SafeError("secure_vault_unavailable")

def secret(name, value=None):
    k = vault()
    if value is None: return k.get_password(SERVICE, name)
    k.set_password(SERVICE, name, value)

def hidden_input(label):
    # GUI is best effort; never claim every host supports a popup.
    try:
        import tkinter as tk
        from tkinter import simpledialog
        win = tk.Tk(); win.withdraw()
        value = simpledialog.askstring("Private local credential", label, show="*", parent=win)
        win.destroy()
        if value: return value
        raise SafeError("credential_entry_cancelled")
    except ImportError: pass
    except Exception as e:
        if isinstance(e, SafeError) and str(e) == "credential_entry_cancelled": raise
    if not sys.stdin.isatty(): raise SafeError("secure_interactive_input_required")
    return getpass.getpass(label + ": ")

def choose_client():
    try:
        import tkinter as tk
        from tkinter import filedialog
        win = tk.Tk(); win.withdraw()
        path = filedialog.askopenfilename(title="Choose your Desktop OAuth client JSON", filetypes=[("JSON", "*.json")]); win.destroy()
    except Exception:
        if not sys.stdin.isatty(): raise SafeError("client_file_picker_unavailable")
        path = input("Path to your own Desktop OAuth client JSON: ").strip()
    if not path: raise SafeError("client_selection_cancelled")
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if "installed" not in value: raise SafeError("desktop_oauth_client_required")
    return value

def connect(service):
    if service in ("semrush", "ads-token"):
        secret(service, hidden_input("Semrush API key" if service == "semrush" else "Google Ads developer token"))
        return {"stored": service, "storage": "OS credential vault", "live_access_verified": False}
    from google_auth_oauthlib.flow import InstalledAppFlow
    vault()  # Verify secure storage before opening consent.
    client = choose_client()
    flow = InstalledAppFlow.from_client_config(client, SCOPES[service], autogenerate_code_verifier=True)
    credentials = flow.run_local_server(host="localhost", port=0, open_browser=True, access_type="offline", prompt="consent", authorization_prompt_message="", success_message="Authorization complete. You may close this window.")
    secret(service + "-oauth", credentials.to_json())
    return {"connected": service, "storage": "OS credential vault", "live_access_verified": False}

def credentials(service):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    value = secret(service + "-oauth")
    if not value: raise SafeError("oauth_connection_required")
    c = Credentials.from_authorized_user_info(json.loads(value), SCOPES[service])
    if c.expired and c.refresh_token:
        c.refresh(Request()); secret(service + "-oauth", c.to_json())
    return c

def windows(tz, now=None):
    today = (now or datetime.now(ZoneInfo(tz))).date(); end = today - timedelta(days=1)
    return [("recent7", end-timedelta(days=6), end), ("previous7", end-timedelta(days=13), end-timedelta(days=7)), ("recent28", end-timedelta(days=27), end)]

def ga4(paths):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, Filter, FilterExpression, FilterExpressionList
    c = config()
    for k in ("ga4_property_id", "ga4_host", "ga4_timezone"):
        if not c.get(k): raise SafeError("configuration_required_" + k)
    client = BetaAnalyticsDataClient(credentials=credentials("ga4"))
    # Actual metadata report verifies property timezone and domain before comparing windows.
    probe_request = RunReportRequest(property="properties/"+c["ga4_property_id"], date_ranges=[DateRange(start_date="yesterday", end_date="yesterday")], dimensions=[Dimension(name="hostName")], metrics=[Metric(name="screenPageViews")], limit=10000)
    probe = client.run_report(probe_request)
    observed_tz = probe.metadata.time_zone
    if observed_tz != c["ga4_timezone"]: raise SafeError("property_timezone_mismatch")
    def exact(field, value): return FilterExpression(filter=Filter(field_name=field, string_filter=Filter.StringFilter(match_type=Filter.StringFilter.MatchType.EXACT, value=value)))
    filters = [exact("hostName", c["ga4_host"])]
    if paths: filters.append(FilterExpression(or_group=FilterExpressionList(expressions=[exact("pagePath", p) for p in paths])))
    results=[]
    for label,start,end in windows(observed_tz):
        offset=0; reports=[]
        while True:
            req=RunReportRequest(property="properties/"+c["ga4_property_id"], date_ranges=[DateRange(start_date=str(start),end_date=str(end))], dimensions=[Dimension(name="hostName"),Dimension(name="pagePath")], metrics=[Metric(name="screenPageViews")], dimension_filter=FilterExpression(and_group=FilterExpressionList(expressions=filters)), offset=offset,limit=10000)
            response=client.run_report(req)
            reports.append({"request":type(req).to_dict(req),"response":type(response).to_dict(response)})
            offset += len(response.rows)
            if offset >= response.row_count: break
            if not response.rows: raise SafeError("unexpected_empty_page")
        results.append({"window":label,"start":str(start),"end":str(end),"reports":reports})
    return {"provider":"GA4 Data API","probe":{"request":type(probe_request).to_dict(probe_request),"response":type(probe).to_dict(probe)},"host":c["ga4_host"],"timezone":observed_tz,"metric":"screenPageViews","extracted_at":datetime.now().astimezone().isoformat(),"windows":results,"notes":"Inspect metadata for thresholding/sampling; absent rows are not zero. Host filter is exact; empty results do not prove a domain match."}

def semrush(keywords):
    key=secret("semrush")
    if not key: raise SafeError("semrush_connection_required")
    reports=[]
    for keyword in keywords:
        params={"type":"phrase_this","key":key,"phrase":keyword,"database":"kr","export_columns":"Ph,Nq,Cp,Co,Nr,Td"}
        # Never persist URL: it contains the key.
        with urlopen("https://api.semrush.com/?"+urlencode(params), timeout=45) as response: body=response.read().decode("utf-8-sig")
        if body.startswith("ERROR"):
            # Semrush errors can describe quota/no-results; safe numeric code only.
            code=body.split("::",1)[0].strip()
            reports.append({"request":{k:v for k,v in params.items() if k != "key"},"keyword":keyword,"status":"provider_error","code":code if code.startswith("ERROR ") and code[6:].isdigit() else "ERROR","fallback_review_required":True})
        else:
            rows=list(csv.DictReader(io.StringIO(body), delimiter=";"))
            reports.append({"request":{k:v for k,v in params.items() if k != "key"},"keyword":keyword,"status":"returned" if rows else "no_rows","rows":rows})
    return {"provider":"Semrush","database":"kr","extracted_at":datetime.now().astimezone().isoformat(),"reports":reports,"note":"No rows are not zero. Judge core-word sufficiency before fallback; valid low volume is not a fallback reason."}

def ads(keywords, reason):
    if reason not in ("semrush_unavailable","semrush_quota_exhausted","semrush_data_insufficient_for_core_keywords"):
        raise SafeError("valid_fallback_reason_required")
    from google.ads.googleads.client import GoogleAdsClient
    from google.protobuf.json_format import MessageToDict
    c=config(); token=secret("ads-token")
    if not token or not c.get("google_ads_customer_id"): raise SafeError("ads_configuration_required")
    oauth=credentials("ads")
    kwargs={"credentials":oauth,"developer_token":token,"use_proto_plus":True}
    if c.get("google_ads_login_customer_id"): kwargs["login_customer_id"]=c["google_ads_login_customer_id"].replace("-", "")
    client=GoogleAdsClient(**kwargs)
    request=client.get_type("GenerateKeywordHistoricalMetricsRequest")
    request.customer_id=c["google_ads_customer_id"].replace("-", "")
    request.keywords.extend(keywords);request.geo_target_constants.append("geoTargetConstants/2410");request.language="languageConstants/1012"
    request.keyword_plan_network=client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    response=client.get_service("KeywordPlanIdeaService").generate_keyword_historical_metrics(request=request)
    return {"provider":"Google Ads Keyword Planner","geo":"South Korea/2410","language":"Korean/1012","network":"GOOGLE_SEARCH","fallback_reason":reason,"extracted_at":datetime.now().astimezone().isoformat(),"request":MessageToDict(request._pb, preserving_proto_field_name=True),"response":MessageToDict(response._pb, preserving_proto_field_name=True)}

def has_module(name):
    try: return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError): return False

def doctor():
    modules={n:has_module(n) for n in ("google.auth","google_auth_oauthlib","google.analytics.data_v1beta","google.ads.googleads","keyring","docx","PIL")}
    store=False; connections={n:False for n in ("ga4-oauth","ads-oauth","semrush","ads-token")}
    if modules["keyring"]:
        try:
            k=vault();store=True
            connections={n:bool(k.get_password(SERVICE,n)) for n in connections}
        except Exception: pass
    return {"python":sys.version.split()[0],"python_supported":sys.version_info >= (3,11),"dependencies":modules,"secure_vault_available":store,"connections_present_not_verified":connections,"config_present":(LOCAL/"config.json").exists(),"libreoffice_available":bool(shutil.which("soffice")),"network_performed":False,"next":"Read knowledge/connections.md; connect missing services, then query to verify access."}

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="command",required=True)
    d=sub.add_parser("doctor");d.add_argument("--json",action="store_true")
    f=sub.add_parser("configure");f.add_argument("--property");f.add_argument("--host");f.add_argument("--timezone");f.add_argument("--ads-customer");f.add_argument("--ads-login-customer")
    c=sub.add_parser("connect");c.add_argument("service",choices=["ga4","ads","semrush","ads-token"])
    q=sub.add_parser("query");q.add_argument("service",choices=["ga4","semrush","ads"]);q.add_argument("--keywords",nargs="+",default=[]);q.add_argument("--paths",nargs="+",default=[]);q.add_argument("--fallback-reason");q.add_argument("--out",required=True)
    a=ap.parse_args()
    try:
        if a.command=="doctor": result=doctor()
        elif a.command=="configure":
            value=config()
            for attr,key in (("property","ga4_property_id"),("host","ga4_host"),("timezone","ga4_timezone"),("ads_customer","google_ads_customer_id"),("ads_login_customer","google_ads_login_customer_id")):
                if getattr(a,attr): value[key]=getattr(a,attr)
            if value.get("ga4_timezone"): ZoneInfo(value["ga4_timezone"])
            save(LOCAL/"config.json",value);result={"configuration_saved":True}
        elif a.command=="connect": result=connect(a.service)
        else:
            out=(ROOT/a.out).resolve()
            if not out.is_relative_to(ROOT/"work") and not out.is_relative_to(LOCAL): raise SafeError("output_must_be_private_work_or_local")
            if a.service != "ga4" and not a.keywords: raise SafeError("keywords_required")
            result=ga4(a.paths) if a.service=="ga4" else semrush(a.keywords) if a.service=="semrush" else ads(a.keywords,a.fallback_reason)
            save(out,result);result={"saved":out.relative_to(ROOT).as_posix(),"live_query_completed":True,"content_check_required":True}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as e:
        # No raw exception text: HTTP/OAuth exceptions may contain credentials.
        code=str(e) if isinstance(e,SafeError) and str(e).replace("_", "").isalnum() else "connection_or_environment_failure"
        print(json.dumps({"error":code,"exception_type":type(e).__name__,"credential_values_suppressed":True}));return 1
    return 0
if __name__=="__main__":sys.exit(main())
