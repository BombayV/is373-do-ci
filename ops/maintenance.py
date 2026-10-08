#!/usr/bin/python3
"""Refresh container base images weekly after a verified database backup."""
import subprocess

def run(*args):
    subprocess.run(args, check=True, timeout=1200)
run('/usr/bin/python3', '/usr/local/lib/is373/backup.py')
run('docker', 'compose', '-f', '/home/bombayv/is373-do-ci/docker-compose.yml', 'pull')
run('docker', 'compose', '-f', '/home/bombayv/is373-do-ci/docker-compose.yml', 'up', '-d', '--wait')
run('docker', 'compose', '-f', '/home/bombayv/traefik/docker-compose.yml', 'pull')
run('docker', 'compose', '-f', '/home/bombayv/traefik/docker-compose.yml', 'up', '-d')
run('/usr/bin/python3', '/usr/local/lib/is373/health.py')
