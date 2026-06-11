"""Run AnotherEden and JoJo SS scrapers sequentially"""
import subprocess, sys, os, time

LOG = "../run_ae_jojo_log.txt"
SCRAPERS = ["another_eden_scraper.py", "jojo_ss_scraper.py"]

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open(LOG, "w", encoding="utf-8") as log:
    for scraper in SCRAPERS:
        log.write(f"\n{'='*50}\nRunning: {scraper}\n{'='*50}\n")
        log.flush()
        t0 = time.time()
        result = subprocess.run(
            [sys.executable, scraper],
            capture_output=True, encoding="utf-8", errors="replace"
        )
        elapsed = int(time.time() - t0)
        log.write(result.stdout)
        if result.returncode != 0 and "UnicodeEncodeError" not in result.stderr:
            log.write(f"STDERR:\n{result.stderr}\n")
        log.write(f"Exit: {result.returncode} | Time: {elapsed}s\n")
        log.flush()

print("All done. See run_ae_jojo_log.txt")
