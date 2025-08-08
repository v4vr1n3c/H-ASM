import os, subprocess, shlex

def run_nuclei(target_url: str):
    # MVP: if nuclei binary is present at /usr/bin/nuclei or in tools/, run it.
    # Otherwise, just return a mocked result.
    nuclei_path = "/usr/bin/nuclei"
    templates = os.getenv("NUCLEI_TEMPLATES_PATH", "/tools/nuclei-templates")
    if os.path.exists(nuclei_path):
        cmd = f"{shlex.quote(nuclei_path)} -u {shlex.quote(target_url)} -t {shlex.quote(templates)} -json"
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            return proc.stdout
        except Exception as e:
            return {"error": str(e)}
    # mock
    return [{"target": target_url, "template": "mock-template", "severity": "medium", "info": "mocked"}]
