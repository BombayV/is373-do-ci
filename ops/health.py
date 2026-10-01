#!/usr/bin/python3
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request

for name in ['traefik', 'it373_fastapi_app']:
    state = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]['State']
    assert state['Running'], name + ' is down'
    if 'Health' in state:
        assert state['Health']['Status'] == 'healthy', name + ' is unhealthy'
assert shutil.disk_usage('/').free / shutil.disk_usage('/').total > .15, 'Disk space below 15%'
request = urllib.request.Request('https://is373.bombayv.com/', headers={'User-Agent': 'Mozilla/5.0 IS373-HealthCheck'})
with urllib.request.urlopen(request, timeout=30) as response:
    assert response.status == 200 and b'Task Dashboard' in response.read(), 'Website check failed'
status = json.loads(Path('/var/lib/is373-monitor/backup-status.json').read_text())
age = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(status['last_success'])
assert age.total_seconds() < 27 * 3600, 'Off-VM backup is overdue'
print('Website, containers, disk space, and off-VM backup are healthy.')
