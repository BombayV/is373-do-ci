"""Exercise the running image, including validation and persisted SQLite writes."""
import argparse
import time
import urllib.error
import urllib.parse
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:18000")
parser.add_argument("--verify-only", action="store_true")
args = parser.parse_args()
url = args.url.rstrip("/")
marker = "CI persistence verification"

def get_dashboard():
    with urllib.request.urlopen(url + "/", timeout=5) as response:
        assert response.status == 200
        return response.read().decode()

for attempt in range(90):
    try:
        page = get_dashboard()
        break
    except (urllib.error.URLError, TimeoutError):
        if attempt == 89:
            raise
        time.sleep(1)
assert "Task Dashboard" in page, "Dashboard did not render"
if not args.verify_only:
    invalid = urllib.parse.urlencode({"title": marker}).encode()
    try:
        urllib.request.urlopen(url + "/items", data=invalid, timeout=10)
    except urllib.error.HTTPError as error:
        assert error.code == 422, "Missing description should fail validation"
    else:
        raise AssertionError("Invalid form was accepted")
    valid = urllib.parse.urlencode({"title": marker, "description": "Saved by the image validation job"}).encode()
    with urllib.request.urlopen(url + "/items", data=valid, timeout=10) as response:
        assert response.status == 200
        assert marker in response.read().decode(), "Created item missing from response"
assert marker in get_dashboard(), "Saved item missing from database"
print("Dashboard and SQLite persistence verified." if args.verify_only else "Dashboard, invalid form rejection, and item creation verified.")
