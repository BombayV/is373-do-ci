#!/usr/bin/python3
"""Back up SQLite online, validate a restored copy, and push to a private repo."""
import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile

repo = Path('/var/lib/is373-backups')
status = Path('/var/lib/is373-monitor/backup-status.json')
env = dict(os.environ, GIT_SSH_COMMAND='ssh -i /home/bombayv/.ssh/is373_backups -o IdentitiesOnly=yes -o UserKnownHostsFile=/home/bombayv/.ssh/known_hosts -o StrictHostKeyChecking=yes')
def run(*args):
    return subprocess.check_output(args, env=env, text=True).strip()
if not (repo / '.git').exists():
    run('git', 'clone', 'git@github.com:BombayV/is373-backups.git', str(repo))
repo.chmod(0o700)
run('git', '-C', str(repo), 'config', 'user.name', 'IS373 Backup')
run('git', '-C', str(repo), 'config', 'user.email', 'backup@is373.bombayv.com')
if run('git', '-C', str(repo), 'ls-remote', 'origin', 'refs/heads/main'):
    run('git', '-C', str(repo), 'pull', '--ff-only', 'origin', 'main')
source = Path(run('docker', 'volume', 'inspect', 'it373-do-ci_sqlite_data', '--format', '{{.Mountpoint}}')) / 'app.db'
(repo / 'snapshots').mkdir(exist_ok=True)
now = datetime.datetime.now(datetime.timezone.utc)
target = repo / 'snapshots' / (now.strftime('%Y-%m-%d') + '.sqlite3')
with sqlite3.connect('file:' + str(source) + '?mode=ro', uri=True) as src, sqlite3.connect(str(target)) as dst:
    src.backup(dst)
with tempfile.TemporaryDirectory() as tmp:
    restored = Path(tmp) / 'restored.sqlite3'
    shutil.copy2(target, restored)
    with sqlite3.connect(str(restored)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Backup restore integrity check failed')
        db.execute('SELECT count(*) FROM items').fetchone()
for old in (repo / 'snapshots').glob('*.sqlite3'):
    if (now.date() - datetime.date.fromisoformat(old.stem)).days > 30:
        old.unlink()
(repo / 'README.md').write_text('Private daily SQLite backups for is373.bombayv.com. Each backup is checked using SQLite integrity_check and a restore query. The working tree retains 30 days; older copies remain in Git history. Restore: stop the app, copy a snapshot into its SQLite volume as app.db, chown to 10001:10001, and start the app. Never restore over a running database.\n')
run('git', '-C', str(repo), 'add', 'snapshots', 'README.md')
if run('git', '-C', str(repo), 'status', '--porcelain'):
    run('git', '-C', str(repo), 'commit', '-m', 'Verified SQLite backup ' + now.isoformat())
run('git', '-C', str(repo), 'push', 'origin', 'HEAD:main')
status.parent.mkdir(exist_ok=True, mode=0o755)
status.write_text(json.dumps({'last_success': now.isoformat(), 'restore_verified': True}) + '\n')
status.chmod(0o644)
print('Backup pushed; restore integrity verified.')
