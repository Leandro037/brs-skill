from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from brs.builtin_profiles import (
    make_code_profile,
    make_json_profile,
    make_research_document_profile,
)
from brs.factory import brs_from_profile

TYPE_MAP = {
    "str": str, "string": str,
    "int": int, "integer": int,
    "float": float,
    "bool": bool, "boolean": bool,
    "dict": dict, "object": dict,
    "list": list, "array": list,
}

def serialize_result(result) -> dict[str, Any]:
    return {
        "decision": result.decision.value,
        "artifact": result.artifact,
        "checks": [
            {
                "check_id": c.check_id,
                "status": c.status.value,
                "evidence": c.evidence,
                "mandatory": c.mandatory,
                "repairable": c.repairable,
                "metadata": c.metadata,
            }
            for c in result.checks
        ],
        "failed_checks": [c.check_id for c in result.failed_checks],
        "repair_attempts": result.repair_attempts,
        "iterations": result.iterations,
        "trace": [
            {"event": e.event, "iteration": e.iteration, "payload": e.payload}
            for e in result.trace
        ],
    }

def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    profile_name = str(payload.get("profile", "")).strip().lower()
    artifact_text = payload.get("artifact", "")
    if not isinstance(artifact_text, str):
        return {"decision":"BLOCK","error":"artifact must be text","checks":[],"failed_checks":["PLAYGROUND_INPUT"],"repair_attempts":0,"iterations":0,"trace":[]}

    try:
        if profile_name == "json":
            try:
                artifact = json.loads(artifact_text)
            except json.JSONDecodeError as exc:
                return {
                    "decision":"BLOCK",
                    "artifact":artifact_text,
                    "checks":[{
                        "check_id":"JSON_PARSE",
                        "status":"FAIL",
                        "evidence":f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
                        "mandatory":True,
                        "repairable":False,
                        "metadata":{"line":exc.lineno,"column":exc.colno},
                    }],
                    "failed_checks":["JSON_PARSE"],
                    "repair_attempts":0,
                    "iterations":1,
                    "trace":[{"event":"validation","iteration":1,"payload":{"failed_check_ids":["JSON_PARSE"],"check_count":1}}],
                }
            required_keys = tuple(str(x) for x in payload.get("required_keys", []))
            defaults = payload.get("defaults", {}) or {}
            if not isinstance(defaults, dict):
                raise ValueError("defaults must be a JSON object")
            expected_types = {}
            for field, type_name in (payload.get("expected_types", {}) or {}).items():
                key = str(type_name).strip().lower()
                if key not in TYPE_MAP:
                    raise ValueError(f"unsupported type for {field}: {type_name}")
                expected_types[str(field)] = TYPE_MAP[key]
            profile = make_json_profile(required_keys=required_keys, expected_types=expected_types, defaults=defaults)
            engine, context = brs_from_profile(profile, max_repair_iterations=1)

        elif profile_name in {"code", "python", "code-python"}:
            artifact = artifact_text
            profile = make_code_profile(language="python")
            engine, context = brs_from_profile(profile)

        elif profile_name in {"research", "research-document", "document"}:
            artifact = artifact_text
            required_sections = tuple(str(x) for x in payload.get("required_sections", ["Abstract","Method","Results","Limitations"]))
            profile = make_research_document_profile(
                required_sections=required_sections,
                require_references=bool(payload.get("require_references", True)),
            )
            engine, context = brs_from_profile(profile)

        else:
            raise ValueError("profile must be json, code, or research")

        result = engine.validate(artifact, context=context)
        response = serialize_result(result)
        response["profile"] = profile.name
        return response
    except (TypeError, ValueError) as exc:
        return {"decision":"BLOCK","error":str(exc),"checks":[],"failed_checks":["PLAYGROUND_CONFIGURATION"],"repair_attempts":0,"iterations":0,"trace":[]}

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BRS Playground</title>
<style>
:root{--bg:#f4f7f5;--panel:#fff;--ink:#15211c;--muted:#68746e;--line:#dce4df;--green:#117653;--red:#b43b38}
*{box-sizing:border-box}body{margin:0;font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--ink)}
main{max-width:1100px;margin:auto;padding:34px 18px 60px}h1{font-size:38px;margin:0 0 5px}h1 span{color:var(--green)}.sub{color:var(--muted);max-width:760px;margin-bottom:24px}
.grid{display:grid;grid-template-columns:1.05fr .95fr;gap:18px}.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px}
label{display:block;font-weight:650;margin:12px 0 6px}select,input,textarea,button{font:inherit}select,input,textarea{width:100%;border:1px solid #cdd8d2;border-radius:10px;padding:10px;background:white}
textarea{min-height:310px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;resize:vertical}button{border:0;border-radius:10px;background:var(--green);color:white;padding:11px 16px;font-weight:700;cursor:pointer;margin-top:12px}
.preset{background:#e9f0ed;color:#23463a;margin-right:6px}.status{font-size:27px;font-weight:800}.release{color:var(--green)}.block{color:var(--red)}
.check{border-top:1px solid var(--line);padding:11px 0}.pass{color:var(--green);font-weight:800}.fail{color:var(--red);font-weight:800}.small{font-size:13px;color:var(--muted)}
pre{white-space:pre-wrap;word-break:break-word;background:#f6f8f7;border-radius:10px;padding:12px;max-height:270px;overflow:auto}.options{display:grid;grid-template-columns:1fr 1fr;gap:10px}.hidden{display:none}
@media(max-width:800px){.grid{grid-template-columns:1fr}.options{grid-template-columns:1fr}h1{font-size:31px}}
</style>
</head><body><main>
<h1>BRS <span>Playground</span></h1>
<p class="sub">Test Binary Review Swarm as a pre-release validation layer. Inspect RELEASE/BLOCK, check evidence, repair attempts, and the final artifact.</p>
<div class="grid"><section class="card">
<label>Profile</label><select id="profile"><option value="json">JSON</option><option value="code">Python code</option><option value="research">Research document</option></select>
<div id="jsonOptions"><div class="options"><div><label>Required keys</label><input id="required" value="name,repetitions"></div><div><label>Defaults (JSON)</label><input id="defaults" value='{"name":"untitled","repetitions":5}'></div></div>
<label>Expected types (JSON map)</label><input id="types" value='{"name":"str","repetitions":"int"}'></div>
<div id="researchOptions" class="hidden"><label>Required sections</label><input id="sections" value="Abstract,Method,Results,Limitations"></div>
<label>Artifact</label><textarea id="artifact"></textarea>
<div><button class="preset" id="validPreset" type="button">Load valid example</button><button class="preset" id="invalidPreset" type="button">Load invalid example</button></div>
<button id="validate" type="button">Validate with BRS</button></section>
<section class="card"><div id="decision" class="status">Not validated</div><p id="summary" class="small">Results will appear here.</p><div id="checks"></div>
<h3>Final artifact</h3><pre id="finalArtifact">—</pre><h3>Trace</h3><pre id="trace">—</pre></section></div>
</main>
<script>
const $=id=>document.getElementById(id);
const presets={
json:{valid:'{"name":"lateral_raise","repetitions":5}',invalid:'{"repetitions":3}'},
code:{valid:'def add(a, b):\\n    return a + b\\n',invalid:'def broken(:\\n    pass\\n'},
research:{valid:'# Study\\n\\n## Abstract\\nSummary.\\n\\n## Method\\nMethod.\\n\\n## Results\\nResults.\\n\\n## Limitations\\nInternal only.\\n\\n## References\\n- Reference.',invalid:'# Study\\n\\n## Abstract\\nSummary.\\n\\n## Method\\nMethod.\\n'}
};
function sync(){const p=$('profile').value;$('jsonOptions').classList.toggle('hidden',p!=='json');$('researchOptions').classList.toggle('hidden',p!=='research');$('artifact').value=presets[p].valid}
$('profile').addEventListener('change',sync);$('validPreset').addEventListener('click',()=>{$('artifact').value=presets[$('profile').value].valid});$('invalidPreset').addEventListener('click',()=>{$('artifact').value=presets[$('profile').value].invalid});
$('validate').addEventListener('click',async()=>{let body={profile:$('profile').value,artifact:$('artifact').value};
if(body.profile==='json'){body.required_keys=$('required').value.split(',').map(x=>x.trim()).filter(Boolean);try{body.defaults=JSON.parse($('defaults').value||'{}');body.expected_types=JSON.parse($('types').value||'{}')}catch(e){alert('JSON options are invalid');return}}
if(body.profile==='research'){body.required_sections=$('sections').value.split(',').map(x=>x.trim()).filter(Boolean);body.require_references=true}
const res=await fetch('/api/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await res.json();
const d=$('decision');d.textContent=data.decision||'BLOCK';d.className='status '+(data.decision==='RELEASE'?'release':'block');
$('summary').textContent=(data.checks?.length||0)+' checks · '+(data.repair_attempts||0)+' repairs · '+(data.iterations||0)+' validation rounds';
$('checks').innerHTML=(data.checks||[]).map(c=>'<div class="check"><span class="'+(c.status==='PASS'?'pass':'fail')+'">'+c.status+'</span> <b>'+c.check_id+'</b><div class="small">'+escapeHtml(c.evidence||'')+'</div></div>').join('')||'<div class="small">'+escapeHtml(data.error||'No checks')+'</div>';
$('finalArtifact').textContent=typeof data.artifact==='string'?data.artifact:JSON.stringify(data.artifact,null,2);$('trace').textContent=JSON.stringify(data.trace||[],null,2)});
function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}sync();
</script></body></html>"""

class PlaygroundHandler(BaseHTTPRequestHandler):
    def _send(self,status:int,body:bytes,content_type:str)->None:
        self.send_response(status);self.send_header("Content-Type",content_type);self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self)->None:
        if self.path=="/": self._send(200,HTML.encode("utf-8"),"text/html; charset=utf-8")
        elif self.path=="/health": self._send(200,b'{"status":"ok"}',"application/json")
        else: self._send(404,b"not found","text/plain; charset=utf-8")
    def do_POST(self)->None:
        if self.path!="/api/validate": self._send(404,b'{"error":"not found"}',"application/json");return
        try:
            length=int(self.headers.get("Content-Length","0"));raw=self.rfile.read(min(length,1_000_000));payload=json.loads(raw.decode("utf-8"))
            if not isinstance(payload,dict): raise ValueError("request body must be a JSON object")
            body=json.dumps(validate_payload(payload),ensure_ascii=False,indent=2,default=str).encode("utf-8");self._send(200,body,"application/json; charset=utf-8")
        except Exception as exc:
            body=json.dumps({"decision":"BLOCK","error":str(exc)}).encode("utf-8");self._send(400,body,"application/json; charset=utf-8")
    def log_message(self,format:str,*args:Any)->None: return

def main()->None:
    parser=argparse.ArgumentParser(description="Run BRS Playground");parser.add_argument("--host",default="127.0.0.1");parser.add_argument("--port",default=8000,type=int);args=parser.parse_args()
    server=ThreadingHTTPServer((args.host,args.port),PlaygroundHandler);print(f"BRS Playground running at http://{args.host}:{args.port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=="__main__": main()
