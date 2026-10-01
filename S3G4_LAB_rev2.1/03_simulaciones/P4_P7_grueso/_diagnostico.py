from pathlib import Path
import subprocess, time, re, sys

ROOT = Path(__file__).resolve().parent
EXE = Path(r"C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe")
patterns = sys.argv[1:] or ["P4_rele/T*.asc", "P7_sin_rele/T*.asc"]
files = sorted({p for pattern in patterns for p in ROOT.glob(pattern)})
for asc in files:
    t = time.monotonic()
    try:
        p = subprocess.run([EXE, "-b", asc], capture_output=True, text=True, timeout=180)
        code = p.returncode
        proc = ""
    except subprocess.TimeoutExpired:
        code, proc = 124, " TIMEOUT"
    log = asc.with_suffix(".log")
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    issues = [x for x in text.splitlines() if re.search(r"error|warning|fatal|unknown|no such|failed", x, re.I)]
    print(f"{asc.relative_to(ROOT)} exit={code} sec={time.monotonic()-t:.1f} issues={len(issues)}{proc}", flush=True)
    for line in issues[:8]:
        print("  " + line, flush=True)
