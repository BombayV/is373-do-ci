# IS373 — FastAPI deployment evidence

A FastAPI and SQLite task dashboard deployed with GitHub Actions, Docker Compose, and Traefik HTTPS. Deployment evidence below was verified on **October 8, 2026**.

## VM GCloud
Instead of paying for DigitalOcean, Google offers $300 in credits that can be used for anyone.
<img width="1334" height="1042" alt="Screenshot 2026-10-08 at 2 04 03 PM" src="https://github.com/user-attachments/assets/7ede1711-6430-45d7-8708-7828267b2046" />


## Environments and successful deployments

- **QA:** [qa.is373-test.bombayv.com](https://qa.is373-test.bombayv.com/) — branch `qa`; [successful QA workflow run](https://github.com/BombayV/is373-do-ci/actions/runs/37819589097).
- **Production:** [is373-test.bombayv.com](https://is373-test.bombayv.com/) — branch `main`; [successful production workflow run](https://github.com/BombayV/is373-do-ci/actions/runs/37819589095). This is the main deployment on the replacement VM, despite the hostname containing “test.”
- Both runs deployed commit [`e38c36a92178b2d2bf67f8ea9d047f54320dd269`](https://github.com/BombayV/is373-do-ci/commit/e38c36a92178b2d2bf67f8ea9d047f54320dd269), which enabled branch-specific deployment and separate QA application/database resources.

## Image location and deployed tags

**Image registry location: none configured.** The workflow builds images directly on the GCP VM and stores them in that VM's Docker image store. It does not push to Docker Hub, GHCR, or Google Artifact Registry; there is no published application image URL.

- QA image: `is373-qa-web:latest`; image ID `sha256:038688be9a5c7bad369c12455aabcd53389b598c1be379a843b6b846a4aa4b28`.
- Production image: `it373-do-ci-web:latest`; image ID `sha256:3be04774fa6661e53d758cf77fd135f5bb13c72bafd09dd9dcab8e5b6009688f`.

`latest` is mutable. The full commit and image IDs above identify the verified deployment; later builds can replace these tags. QA and production build independently rather than promoting a single registry artifact.

## Screenshots: QA, then production

These screenshots show the resulting deployment in QA and production, captured in that order. They show the same application at the verified commit, with separate databases: QA starts empty and production retains its two restored items. They are current-state evidence, not a before/after recording of a visual feature change. The existing dashboard banner still mentions the old `is373.bombayv.com` hostname; use the environment links above for the active addresses.

### QA

[Open QA](https://qa.is373-test.bombayv.com/)

<img width="412" height="504" alt="image" src="https://github.com/user-attachments/assets/a26060b9-b24e-44fe-b671-ccca75e8f7c4" />


### Production

[Open production](https://is373-test.bombayv.com/)

<img width="412" height="504" alt="image" src="https://github.com/user-attachments/assets/74ffa1ae-dc7e-4cdd-9c40-c5c61f052f6f" />


## Non-root SSH and authentication restrictions

The administration and deployment account is `bombayv`. The MacBook uses its existing Ed25519 key; GitHub Actions uses a separate deployment key. Only public keys are authorized on the VM. The VM has a separate read-only GitHub repository deploy key for fetching code. No credentials are included in this README or its evidence files.

<img width="1281" height="913" alt="Screenshot 2026-10-08 at 1 58 58 PM" src="https://github.com/user-attachments/assets/fabe5d4b-3545-434e-b70d-2ebf8bd1e3fe" />

<img width="1281" height="913" alt="Screenshot 2026-10-08 at 1 59 10 PM" src="https://github.com/user-attachments/assets/f896518b-b422-44f0-bcbc-a4ae91efceee" />

<img width="1281" height="913" alt="Screenshot 2026-10-08 at 1 59 44 PM" src="https://github.com/user-attachments/assets/4339b2aa-ca93-4cfd-95da-074cc61bfafb" />

<img width="1281" height="913" alt="Screenshot 2026-10-08 at 2 00 01 PM" src="https://github.com/user-attachments/assets/c752172d-2f4d-4af8-bfe3-d23cd116fda6" />

<img width="1281" height="913" alt="Screenshot 2026-10-08 at 2 00 15 PM" src="https://github.com/user-attachments/assets/c9a1ec8d-02cf-482e-b864-85db7132e3d0" />

## How CI/CD works

The [deployment workflow](.github/workflows/deploy.yml) runs on pushes to `qa` and `main`, and supports manual dispatch. GitHub Actions checks out the repository, connects to the VM as `bombayv` using the repository secrets `GCP_HOST`, `GCP_USER`, and `GCP_SSH_KEY`, and selects the branch-specific checkout. QA pulls `qa` in `/home/bombayv/is373-do-ci-qa`; main and the legacy master trigger pull `main` in `/home/bombayv/is373-do-ci`.

The VM runs `git pull --ff-only`, then `docker compose build --pull`. The [Dockerfile](Dockerfile) installs the pinned Python dependencies, copies the app, and runs it as UID/GID `10001:10001`. Compose starts the container and waits up to 300 seconds for its HTTP health check to pass. Command or health-check failures fail the deployment. There is currently no separate unit-test, lint, image-scan, or registry-push stage.

QA uses container `it373_fastapi_qa` and volume `is373-qa_sqlite_data`; production uses `it373_fastapi_app` and volume `it373-do-ci_sqlite_data`. Traefik routes each hostname to its own container over the shared internal network and terminates HTTPS. A shared deployment concurrency group serializes the two environments on the small VM. Deploying QA does not automatically promote it to production: production deployment requires a push to main or a manual main run.

The separate [health workflow](.github/workflows/monitor.yml) runs approximately every 15 minutes or manually. It verifies the main HTTPS dashboard, running containers, disk space, and freshness of a successful off-VM backup. The VM also checks health every five minutes. Production SQLite backups run daily at 03:00 UTC, validate a restored copy, and push to the private [is373-backups repository](https://github.com/BombayV/is373-backups). QA has its own database and is not included in that production backup job.
