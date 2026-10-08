# IS373 — FastAPI deployment evidence

A FastAPI and SQLite task dashboard deployed with GitHub Actions, Docker Compose, and Traefik HTTPS. Deployment evidence below was verified on **October 8, 2026**.

## VM GCloud
Instead of paying for DigitalOcean, Google offers $300 in credits that can be used for anyone.
<img width="1334" height="1042" alt="Screenshot 2026-10-08 at 2 04 03 PM" src="https://github.com/user-attachments/assets/7ede1711-6430-45d7-8708-7828267b2046" />


## Environments and successful deployments

- **QA:** [qa.is373-test.bombayv.com](https://qa.is373-test.bombayv.com/) — branch `qa`; [successful QA workflow run](https://github.com/BombayV/is373-do-ci/actions/runs/37822480054).
- **Production:** [is373-test.bombayv.com](https://is373-test.bombayv.com/) — branch `main`; [successful production workflow run](https://github.com/BombayV/is373-do-ci/actions/runs/37822934305). This is the main deployment on the replacement VM, despite the hostname containing “test.”
- QA deployed commit [`662893b0e1a912fe60e29787ff765c84abad1be0`](https://github.com/BombayV/is373-do-ci/commit/662893b0e1a912fe60e29787ff765c84abad1be0); production deployed commit [`c1be940d89328c6abfefa070c5095f974201ede4`](https://github.com/BombayV/is373-do-ci/commit/c1be940d89328c6abfefa070c5095f974201ede4). Both linked runs include validation, build, registry push, automatic deployment, and an HTTPS check.

## Image registry and deployed tags

Images are published to **`ghcr.io/bombayv/is373-do-ci`**. The [public GHCR package](https://github.com/BombayV/is373-do-ci/pkgs/container/is373-do-ci) is viewable without signing in.

The [successful registry-based QA run](https://github.com/BombayV/is373-do-ci/actions/runs/37822480054) validated, built, pushed, and automatically deployed commit `662893b0e1a912fe60e29787ff765c84abad1be0`, tagged `sha-662893b0e1a912fe60e29787ff765c84abad1be0`. Its deployed digest is `sha256:a7faa07adfd8c67b8ab4192a8813e67558d6471c1e33cf986c2b180200980a76`.

The [successful registry-based production run](https://github.com/BombayV/is373-do-ci/actions/runs/37822934305) deployed tag `sha-c1be940d89328c6abfefa070c5095f974201ede4`, digest `sha256:ca8b3cdfb61493a5fdb89d150cb2370cceaa7cb2b9b845592a4e325855886f1c`.

Every workflow summary records the full commit, published tag, and image digest. The VM pulls that exact digest rather than rebuilding the application. QA and production build independently rather than promoting one identical digest. See [registry deployment details](docs/REGISTRY-DEPLOYMENT.md) and the [production workflow history](https://github.com/BombayV/is373-do-ci/actions/workflows/deploy.yml?query=branch%3Amain).

## Screenshots: QA, then production

These screenshots show the resulting deployment in QA and production, captured in that order. They show the same application at the verified commit, with separate databases: QA starts empty and production retains its two restored items. They are current-state evidence, not a before/after recording of a visual feature change. These screenshots were captured before registry migration and the later hostname banner update. Both live banners now say `is373-test.bombayv.com`; use the environment links above for the current sites.

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

The [deployment workflow](.github/workflows/deploy.yml) runs on pushes to `qa` or `main` and supports manual dispatch. Pull requests targeting either branch run validation without publishing or deploying. GitHub Actions validates Python syntax, builds the image from the [Dockerfile](Dockerfile), checks dependency compatibility and the non-root image user, and tests dashboard rendering, invalid form rejection, item creation, and SQLite persistence after a restart. A failing check prevents publication and deployment.

After validation, the runner pushes the tested image to GHCR with tag `sha-<full commit>`. The deployment job connects to the VM as `bombayv` using `GCP_HOST`, `GCP_USER`, and `GCP_SSH_KEY`, checks out the exact triggering commit, pulls the published image digest, and starts it with Docker Compose. It waits for container health, then verifies the deployed HTTPS dashboard. Registry access uses a short-lived workflow token in a temporary Docker configuration that is removed afterward; no long-lived registry credential is stored on the VM.

QA uses `/home/bombayv/is373-do-ci-qa`, container `it373_fastapi_qa`, and volume `is373-qa_sqlite_data`. Production uses `/home/bombayv/is373-do-ci`, container `it373_fastapi_app`, and volume `it373-do-ci_sqlite_data`. Traefik routes each hostname to its own container and terminates HTTPS. A shared concurrency group serializes deployments. Validate changes on QA, then merge `qa` into `main` to trigger production. Production builds and tests its own commit-tagged image; it does not automatically deploy when QA changes.

The separate [health workflow](.github/workflows/monitor.yml) runs approximately every 15 minutes or manually. It verifies the main HTTPS dashboard, running containers, disk space, and freshness of a successful off-VM backup. The VM also checks health every five minutes. Production SQLite backups run daily at 03:00 UTC, validate a restored copy, and push to the private [is373-backups repository](https://github.com/BombayV/is373-backups). QA has its own database and is not included in that production backup job.
