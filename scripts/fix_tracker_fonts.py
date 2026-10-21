"""Set font size 10pt on tracker content cells so text fits the tables."""
import json
import subprocess
import sys

EDSDK = r"C:\Users\Administrator\.workbuddy\plugins\cache\workbuddy-builtin\workbuddy-pptx\5.8.3-wb.41334564.gdb0e9b51.h4da087921e4a\skills\workbuddy-pptx\scripts\edsdk.py"
FILE_ID = "41711538-FB89-4036-AA9A-607CD0D11B5A"

# (page_index, shape_id) of the four content tables on each week slide
TARGETS = [
    (13, "00010a"), (13, "00010b"), (13, "00010c"), (13, "00010d"),
    (14, "000112"), (14, "000113"), (14, "000114"), (14, "000115"),
    (16, "00011f"), (16, "000120"), (16, "000121"), (16, "000122"),
]

for page, shape in TARGETS:
    payload = {
        "file_id": FILE_ID,
        "page_index": page,
        "shape_id": shape,
        "start_row": 1,
        "start_col": 0,
        "font_size": 10,
    }
    result = subprocess.run(
        [sys.executable, EDSDK, "call", "slide_set_cell_style", "--json", json.dumps(payload)],
        capture_output=True, text=True,
    )
    print("OK" if '"ok":true' in result.stdout.replace(" ", "") else "FAIL", page, shape,
          result.stdout.strip()[:100], result.stderr.strip()[:100])
