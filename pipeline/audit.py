import json, os, time
def log(event, **kw):
    os.makedirs("out", exist_ok=True)
    with open("out/audit.log", "a") as fh:
        fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **kw}) + "\n")
