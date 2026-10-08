# Registry-based CI/CD

Application images are published to **`ghcr.io/bombayv/is373-do-ci`**.

[Image package](https://github.com/BombayV/is373-do-ci/pkgs/container/is373-do-ci)

Each published image is tagged `sha-<full Git commit>`. Deployment pulls the exact `ghcr.io/bombayv/is373-do-ci@sha256:<digest>` produced by that run, rather than rebuilding on the VM or resolving a mutable tag. The workflow summary records the commit, tag, and digest.

## Validation and delivery

Pushes to `qa` or `main` and manual workflow dispatch validate Python syntax, build the image on a GitHub runner, check dependency compatibility and its non-root user, then test dashboard rendering, rejection of an incomplete form, item creation, and SQLite persistence after a container restart. Pull requests targeting either branch run the same checks without publishing or deploying. Images are pushed only after these checks pass.

The build job authenticates to GHCR with the short-lived GitHub Actions token. A dependent deployment job uses the repository SSH secrets to connect as `bombayv`, checks out the exact triggering commit, authenticates to GHCR using a temporary Docker configuration, pulls the published digest, and waits for container health. The temporary registry credentials are removed when the SSH script exits. A final HTTPS request checks the deployed dashboard.

QA uses `/home/bombayv/is373-do-ci-qa`, container `it373_fastapi_qa`, and database volume `is373-qa_sqlite_data`. Production uses `/home/bombayv/is373-do-ci`, container `it373_fastapi_app`, and database volume `it373-do-ci_sqlite_data`. Successful deployments persist only `APP_IMAGE` in each checkout's ignored `.env` for future restarts. QA's `.env` also sets `COMPOSE_PROJECT_NAME=is373-qa` and `APP_CONTAINER_NAME=it373_fastapi_qa`.

## Promotion and maintenance

Validate a change on QA, then merge `qa` into `main` to trigger production. The main workflow builds and tests its own commit-tagged image; it does not promote the identical QA digest. Both environments deploy published, validated images. Runs are serialized on the shared VM.

Production backup and maintenance timers remain enabled. Weekly maintenance pulls the currently pinned app image and refreshes Traefik; application updates arrive through CI/CD. The production database volume is preserved during deployment.

## Inspect a deployment

Run in the relevant VM checkout:

```bash
cat .env  # project/container names and image digest only; no registry token
docker compose images
docker compose ps
```

Read the image digest and revision directly:

```bash
docker inspect it373_fastapi_qa --format '{{.Config.Image}}'
docker inspect it373_fastapi_app --format '{{.Config.Image}}'
docker image inspect IMAGE_DIGEST --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'
```

If the package remains private, manual pulls require an appropriately authorized registry credential. Automated deployments use the workflow token and do not store a long-lived registry password on the VM.
