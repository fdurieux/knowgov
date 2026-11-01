# The demo's app image: this repository copied in, the harness's dependencies
# at the versions pumllint's record (§12 of its evaluation) names, the J-F
# subject's oracle pins (its kit's contracts/pins.md), and the stdlib web server.
# CPython 3.12: the kit's pins name it, and its verbatim --help texts are
# argparse 3.12's (3.13 wraps seven usage lines differently). Build context is the repository root (see
# docker-compose.override.yml); Dockerfile.dockerignore beside this file keeps
# the backlog, the tests and caches out of it.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    KG_NEO4J_URI=bolt://neo4j:7687 KG_BROWSER_URL=http://localhost:7474 \
    KG_DEMO_RUNS=/repo/runs KG_DEMO_PORT=8080

WORKDIR /repo
COPY . /repo

# pumllint docs/neo4j-governed-knowledge-evaluation.md §12: neo4j 6.4.1, pyyaml, rdflib 7.6.0,
# pyshacl 0.40.2, openai 3.41.0. pumllint itself is a library here: the sequence-diagram mapper
# (harness/extract.py) imports its parser; the released package from PyPI, pinned.
RUN pip install "pumllint==0.33.0" "neo4j==6.4.1" "pyyaml==6.0.3" "rdflib==7.6.0" "pyshacl==0.40.2" "openai==3.41.0" \
 && mkdir -p /repo/runs
# The J-F subject's oracle: its kit's suite (pytest-bdd) over its runtime pins (contracts/pins.md);
# the chain scenarios need bash and GNU timeout, which the base image has.
RUN pip install "pandas==3.0.5" "numpy==2.4.6" "requests==2.34.2" "pyarrow==25.0.1" "pytest==9.1.1" "pytest-bdd==9.0.1"

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=6 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health', timeout=2).status == 200 else 1)"
CMD ["python", "demo/app/server.py"]
