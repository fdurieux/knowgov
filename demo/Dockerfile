# The demo's app image: this repository copied in, the harness's dependencies
# at the versions pumllint's record (§12 of its evaluation) names, the J-F
# subject's oracle pins (its kit's contracts/pins.md), and the stdlib web server.
# CPython 3.12: the kit's pins name it, and its verbatim --help texts are
# argparse 3.12's (3.13 wraps seven usage lines differently). Build context is the repository root (see
# docker-compose.override.yml); Dockerfile.dockerignore beside this file keeps
# the backlog, the tests and caches out of it.
# python:3.12-slim, pinned by its index digest (task-0092); Dependabot's docker entry moves it
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    KG_NEO4J_URI=bolt://neo4j:7687 KG_BROWSER_URL=http://localhost:7474 \
    KG_DEMO_RUNS=/repo/runs KG_DEMO_PORT=8080 \
    KG_PAGE_LISTEN=0.0.0.0

WORKDIR /repo
COPY . /repo

# pumllint docs/neo4j-governed-knowledge-evaluation.md §12: neo4j 6.4.1, pyyaml, rdflib 7.6.0,
# pyshacl 0.40.2, openai 3.41.0. pumllint itself is a library here: the sequence-diagram mapper
# (harness/extract.py) imports its parser; the released package from PyPI, pinned.
RUN pip install "pumllint==0.35.0" "neo4j==6.4.1" "pyyaml==6.0.3" "rdflib==7.6.0" "pyshacl==0.40.2" "openai==3.41.0" \
 && mkdir -p /repo/runs
# The J-F subject's oracle: its kit's suite (pytest-bdd) over its runtime pins (contracts/pins.md);
# the chain scenarios need bash and GNU timeout, which the base image has.
RUN pip install "pandas==3.0.5" "numpy==2.4.6" "requests==2.34.2" "pyarrow==25.0.1" "pytest==9.1.1" "pytest-bdd==9.0.1"

# task-0227: which knowgov this image is, as the page shows it (harness/build_identity.py). Both are
# optional and recorded as given: release.yml passes the tag's commit and the tag; a local build from a
# checkout may pass KG_BUILD_DESCRIBE="$(git describe --tags --always)" through docker-compose.override.yml.
# Without them the page reads the commit from .git's HEAD and refs (Dockerfile.dockerignore lets those in),
# and the distance from the release reads unknown. Last, so a new commit rebuilds only this layer.
ARG KG_BUILD_COMMIT=""
ARG KG_BUILD_DESCRIBE=""
RUN python -c "import json, os; json.dump({'commit': os.environ.get('KG_BUILD_COMMIT') or None, 'describe': os.environ.get('KG_BUILD_DESCRIBE') or None}, open('/repo/.knowgov-build.json', 'w'))"

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=6 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health', timeout=2).status == 200 else 1)"
# the server listens on every interface inside the container; compose publishes it on KG_BIND only, and
# passes KG_BIND in, so the server knows when it reaches beyond the host (task-0096)
CMD ["python", "demo/app/server.py"]
