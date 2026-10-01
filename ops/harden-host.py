#!/usr/bin/python3
"""Run as root on the VM after copying repository ops files to /tmp/is373-ops."""
import json
from pathlib import Path
import shutil
import subprocess

def run(*args):
    subprocess.run(args, check=True)
base = Path('/home/bombayv/traefik')
compose = base / 'docker-compose.yml'
shutil.copy2(compose, base / 'docker-compose.pre-hardening.yml')
compose.write_text('''services:
  traefik:
    image: traefik:v3.7
    container_name: traefik
    restart: always
    user: "10001:10001"
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 192m
    pids_limit: 100
    tmpfs:
      - /tmp:size=16m,mode=1777
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    command:
      - "--api.insecure=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--providers.file.directory=/etc/traefik/dynamic"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./acme.json:/acme.json
      - ./dynamic:/etc/traefik/dynamic:ro
    networks:
      - traefik-proxy
networks:
  traefik-proxy:
    external: true
''')
(base / 'dynamic/https.yml').write_text('''http:
  routers:
    fastapi:
      rule: "Host(`is373.bombayv.com`)"
      entryPoints: [web]
      service: fastapi
      middlewares: [https-redirect]
    fastapi-secure:
      rule: "Host(`is373.bombayv.com`)"
      entryPoints: [websecure]
      service: fastapi
      tls:
        certResolver: letsencrypt
  middlewares:
    https-redirect:
      redirectScheme:
        scheme: https
        permanent: true
  services:
    fastapi:
      loadBalancer:
        servers:
          - url: "http://it373_fastapi_app:8000"
''')
import os
os.chown(base / 'acme.json', 10001, 10001)
(base / 'acme.json').chmod(0o600)
run('docker', 'compose', '-f', str(compose), 'pull')
run('docker', 'compose', '-f', str(compose), 'up', '-d')
config = Path('/etc/docker/daemon.json')
data = json.loads(config.read_text())
data.pop('min-api-version', None)
data['log-driver'] = 'json-file'
data['log-opts'] = {'max-size': '10m', 'max-file': '3'}
config.write_text(json.dumps(data, indent=2) + '\n')
run('dockerd', '--validate', '--config-file', str(config))
run('systemctl', 'restart', 'docker')
Path('/etc/apt/apt.conf.d/52is373-security').write_text('''Unattended-Upgrade::Automatic-Reboot "false";
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
''')
run('systemctl', 'enable', '--now', 'apt-daily.timer', 'apt-daily-upgrade.timer')
lib = Path('/usr/local/lib/is373')
lib.mkdir(parents=True, exist_ok=True)
for name in ['backup.py', 'health.py']:
    shutil.copy2('/tmp/is373-ops/' + name, lib / name)
    (lib / name).chmod(0o755)
Path('/var/lib/is373-monitor').mkdir(exist_ok=True, mode=0o755)
for name, schedule, command in [
    ('is373-backup', 'OnCalendar=*-*-* 03:00:00\nPersistent=true', '/usr/bin/python3 /usr/local/lib/is373/backup.py'),
    ('is373-health', 'OnBootSec=5min\nOnUnitActiveSec=5min', '/usr/bin/python3 /usr/local/lib/is373/health.py'),
]:
    Path('/etc/systemd/system/' + name + '.service').write_text('[Unit]\nDescription=' + name + '\nAfter=docker.service network-online.target\n[Service]\nType=oneshot\nUMask=0077\nExecStart=' + command + '\n')
    Path('/etc/systemd/system/' + name + '.timer').write_text('[Unit]\nDescription=' + name + ' schedule\n[Timer]\n' + schedule + '\n[Install]\nWantedBy=timers.target\n')
run('systemctl', 'daemon-reload')
run('systemctl', 'enable', '--now', 'is373-backup.timer', 'is373-health.timer')
run('systemctl', 'start', 'is373-backup.service')
