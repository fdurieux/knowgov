# The demo's app image: this repository copied in, the harness's dependencies
# at the versions pumllint's record (§12 of its evaluation) names, and the
# stdlib web server. Build context is the repository root (see
# docker-compose.override.yml); Dockerfile.dockerignore beside this file keeps
# the backlog, the tests and caches out of it.
FROM python:3.13-slim

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

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=6 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health', timeout=2).status == 200 else 1)"
CMD ["python", "demo/app/server.py"]
