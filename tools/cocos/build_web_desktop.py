#!/usr/bin/env python3
"""P06/F08: build the Cocos web-desktop package with a reliable exit code and log gate.

The workspace environment sets ELECTRON_RUN_AS_NODE=1, which makes the Electron
editor behave like Node and reject --project; this wrapper removes that variable
(and NODE_OPTIONS, which the editor warns about) only for the child process. It
also passes --disable-gpu-sandbox for the reasons noted at the call site. Exit 0
requires: child return code 0, success marker,
no failure events, and the expected build output present.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_gate():
    import importlib.util
    path = ROOT / "tools/art_gate/build_log_gate.py"
    spec = importlib.util.spec_from_file_location("build_log_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patch_responsive_html(index_path):
    """Make the generated shell fill the browser viewport so real resize events
    can reach Cocos; Cocos still owns design resolution and the rotate notice."""
    index_path = Path(index_path)
    html = index_path.read_text(encoding="utf-8")
    html = html.replace('cc_exact_fit_screen="false" style="width: 1280px; height: 720px;"',
                        'style="width:100vw;height:100vh;"')
    style = ('<style id="responsive-shell">'
             'html,body{margin:0;padding:0;overflow:hidden;background:#1c1b18}'
             '#GameDiv{position:fixed;left:0;top:0;width:100vw!important;height:100vh!important}'
             '#Cocos3dGameContainer,#GameCanvas{position:absolute;left:0;top:0;width:100%!important;height:100%!important}'
             'h1.header,p.footer{display:none!important}'
             '</style>')
    if 'id="responsive-shell"' not in html:
        html = html.replace("</head>", style + "</head>")
    index_path.write_text(html, encoding="utf-8")
    return {"responsive_shell": True, "sha256": __import__("hashlib").sha256(index_path.read_bytes()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--creator", default=str(ROOT / "tools/cocos/editors/3.8.8/CocosCreator.exe"))
    parser.add_argument("--project", default=str(ROOT / "demo"))
    parser.add_argument("--config", default=str(ROOT / "demo/build-config-web-desktop.json"))
    parser.add_argument("--log", default=str(ROOT / "tools/cocos/logs/build_web_desktop.log"))
    parser.add_argument("--expect-output", default=str(ROOT / "demo/build/web-desktop/index.html"))
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.pop("ELECTRON_RUN_AS_NODE", None)
    env.pop("NODE_OPTIONS", None)
    # 2026-10-26: the editor's sandboxed Chromium GPU child process started
    # dying with 0xC0000005 (exit_code=-1073741819) on this host - nine crashes
    # in ~2 s, then "GPU process isn't usable. Goodbye." and exit 2147483651,
    # before the project even loads. Running the GPU thread in the browser
    # process, disabling the GPU sandbox, or forcing SwiftShader each fix it;
    # the built package is byte-identical either way, so this only affects the
    # editor host. Override with COCOS_EXTRA_ARGS if a host does not need it.
    extra = os.environ.get("COCOS_EXTRA_ARGS", "--disable-gpu-sandbox").split()
    command = [args.creator, *extra, "--project", args.project,
               "--build", "configPath=" + args.config]
    started = time.perf_counter()
    try:
        with log_path.open("wb") as log:
            proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                  env=env, timeout=args.timeout)
        code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        code = None
        timed_out = True
    seconds = round(time.perf_counter() - started, 3)

    gate = load_gate()
    if timed_out:
        result = {"status": "fail", "failures": ["build timed out after " + str(args.timeout) + "s"]}
    else:
        result = gate.check_log(log_path, "cocos", code, args.expect_output, [36])
    output_root = Path(args.expect_output).parent
    responsive = patch_responsive_html(args.expect_output) if result.get("status") == "pass" else None
    output_hashes = {}
    for relative in ("index.html", "application.js", "src/settings.json",
                     "src/import-map.json", "assets/main/config.json"):
        path = output_root / relative
        if path.is_file():
            import hashlib
            output_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "kind": "cocos_web_desktop_build",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(command),
        "cocos_exit_code": code,
        "timed_out": timed_out,
        "seconds": seconds,
        "log": str(log_path),
        "gate": result,
        "output_hashes": output_hashes,
        "responsive": responsive,
        "passed": result.get("status") == "pass",
        "meaning": "Build evidence only; not art or engine acceptance.",
    }
    out = ROOT / "delivery/performance" / ("cocos_build_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "exit_code": code, "seconds": seconds,
                      "gate": result.get("status"), "output": str(out)}, ensure_ascii=False))
    if not report["passed"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
