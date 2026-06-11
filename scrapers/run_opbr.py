"""Run OPBR scraper with proper encoding capture"""
import subprocess, sys, os, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting OPBR scraper...")
result = subprocess.run(
    [sys.executable, "one_piece_br_scraper.py"],
    capture_output=True, encoding="utf-8", errors="replace"
)
print(result.stdout[-2000:] if result.stdout else "(no stdout)")
if result.returncode != 0 and "UnicodeEncodeError" not in result.stderr:
    print("STDERR:", result.stderr[-500:])
print(f"Exit: {result.returncode}")
