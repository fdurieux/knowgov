# knowledge_probe

A synthetic, instance-shaped fixture for the MCP reader's knowledge tools (task-0360, task-0361;
decision-0047, decision-0046). Every handle is one of the demo register's synthetic handles
(`demo/register/people/handles.toml`), except `contractor-9`, which the register does not list, on purpose.
Nothing here names a person, an organisation or a client.

- `subjects/knowledge_probe/` an unlisted subject (`listed = false`) on the demo register: five keys
  mapped to CargoQuote's capabilities and modules, three captures and two reviews under `captures/`.
- `code_map.toml` and `code/quote.py` the code leg: `quote.py` maps to APP-0003 and its header cites two keys.
- `expected/` the reports `tools/check_mcp_server.py` holds the reader to, over stdio and HTTP, on the
  rdflib job and on the Neo4j stack job alike: the tools read files only.

`who_knows` reads it with `KG_SUBJECTS=tools/fixtures/knowledge_probe/subjects/knowledge_probe` and
`KG_INSTANCE=tools/fixtures/knowledge_probe`.
