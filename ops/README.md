VM operations

Debian security updates run daily through apt-daily-upgrade; unattended reboots are disabled. Containers refresh weekly on Sunday at 04:00 UTC after a verified backup. Dependabot checks Python, Docker, and GitHub Actions weekly; dependency PRs require review and deployment. Traefik uses file configuration and has no Docker socket mount.

SQLite backups run daily at 03:00 UTC and push only database snapshots to the private BombayV/is373-backups repository through a dedicated write deploy key. Each run restores into a temporary database and checks integrity and the items table. The working tree retains 30 days; Git history retains earlier snapshots. Keys and TLS certificates are not copied into the backup repository.

Health checks run every five minutes on the VM and approximately every 15 minutes in GitHub Actions. They check HTTPS, container state, disk space, and the last successful off-VM backup. Enable GitHub Actions failure notifications in your GitHub notification settings to receive alerts.

Restore: stop web with docker compose stop web; copy the chosen snapshot into the sqlite_data volume as app.db; remove stale app.db-wal and app.db-shm files only after the app is stopped; set owner 10001:10001; restart web and verify HTTPS. Test restores in a separate temporary database first.

Root and password SSH login remain disabled. The rotated bombayv local sudo password is stored only on the operator Mac at ~/.ssh/is373-vm-sudo-password, mode 0600. Keep it in a password manager; it is not committed or used by GitHub deployment.
