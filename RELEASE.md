# Release checklist and packaging

This file describes minimal, reproducible steps used to assemble a release
bundle for Kolibri OS and verify it locally.

1) Preconditions
   - Python `.venv` created and activated (Python 3.10+)
   - All dependencies installed via `pip install -r requirements.txt`

2) Automated checks (local)

```bash
# from repo root
source .venv/bin/activate
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/pyright --outputjson
```

3) Build artifacts

- Create a release archive (tar.gz):

```bash
RELEASE_TAG="kolibri-rc-$(date +%Y%m%d)"
tar -czf ${RELEASE_TAG}.tar.gz .
sha256sum ${RELEASE_TAG}.tar.gz > ${RELEASE_TAG}.sha256
```

4) (Optional) Docker image

If you want to build a backend docker image (requires Docker installed):

```bash
docker build -f backend/Dockerfile -t kolibri-backend:latest backend/
```

5) Publish

- Upload the tarball and checksum to your release server / GitHub Releases.
- Attach Docker image to your registry if built.

6) Notes

- The repository includes typing stubs in `typings/` used by CI to keep `pyright`
  results stable across environments. If you update FastAPI/Pydantic usage,
  update stubs accordingly or pin dependency versions in `requirements.txt`.
