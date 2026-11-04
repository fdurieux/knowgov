#!/bin/sh
# Neo4j's entrypoint in the compose stack (task-0090). The page, Neo4j Browser and bolt are
# published on KG_BIND, 127.0.0.1 unless it names a wider address. On a wider bind this refuses
# to start Neo4j, and with it the whole stack (the app waits for Neo4j's health check), while the
# store's password is the harness default. Otherwise it hands over to the image's own entrypoint.
bind="${KG_BIND:-127.0.0.1}"
case "$bind" in
  127.*|localhost|::1|"[::1]") ;;
  *)
    if [ "${NEO4J_AUTH:-}" = "neo4j/kgpoc2026" ]; then
      echo "knowgov: KG_BIND=$bind publishes the page, Neo4j Browser and bolt beyond this machine," >&2
      echo "knowgov: and the Neo4j password is the default. Refusing to start." >&2
      echo "knowgov: export KG_NEO4J_PASSWORD=<a password of your own>, or leave KG_BIND unset for 127.0.0.1." >&2
      exit 78
    fi
    ;;
esac
exec "$@"
