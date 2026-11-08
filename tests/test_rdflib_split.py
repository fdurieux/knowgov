"""task-0163: the rdflib job split in two parallel jobs, rdflib (the record and its round trip, the job the
ruleset requires by name) and rdflib-readers (the readers). Nothing of the old job is dropped or subset:
every step of it runs in exactly one of the two, the shared setup and the outcome steps in both; both
jobs keep the old job's triggers, environment and pinned setup; security-events: write only where the
action's SARIF step runs."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / ".github" / "workflows" / "harness.yml"

# The rdflib job's steps before the split (main at a743cca), by name, or for an unnamed step its first
# uses: or run: line's first 60 characters.
OLD_STEPS = [
    'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1',
    'actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e',
    'pip install "pumllint==0.35.0" "pyyaml==6.0.3" "rdflib==7.6.',
    'The stdlib suite with the pins, the tests resting on rdflib run here and a skip of one fails (task-0141.01)',
    'S1 to S7 on the in-memory store match the record',
    'The J-F data-load subject, C and D1 to D5, matches its record (D1 skipped across store kinds)',
    "The J-F subject's oracle passes the reference rebuild, every feature, 258 of 258",
    'The minimal subject loads and the gate reports every required key absent',
    'The example instance (task-0006), S1 to S7 from it, match the record and leave it unchanged',
    'A stored document no mapper reads is reported absent by the check and by the load',
    "The subject check (task-0135) with the mappers installed, the public subjects hold with their whole yield, doc-0018's probe is refused and its misspelt key named with the key the documents yield",
    "decision-0009 (a), task-0136, doc-0018's probe given a scenario loads its drafted requirement proposed, not approved, and its misspelt key absent",
    'A register node to the statements its cited anchor names (task-0046), through the rdflib port, S6 with the S1 code as derived',
    "Every subject's citations reach the statements of the documents it loads (task-0077), through the rdflib port, CargoQuote's ENT-0004 on S6 and J-F's ENT-0009 on C through its directory artefacts",
    "The pre-load check (task-0045) through the CI template's script, real pumllint, the example instance clean exits 0, a planted broken PlantUML file exits 1",
    "The pre-load check's baseline (task-0065) on the example instance, real pumllint, the CI template's script, one known finding held exits 0, a second new one exits 1",
    "The pre-load check runs Spectral on api-contracts (task-0066), pinned, through the CI template's script, a clean contract exits 0, a planted broken one exits 1",
    'actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1',
    "The pre-load check runs markdownlint, gplint, bpmnlint and dmnlint (task-0082), pinned, through the CI template's script, a clean file of each kind exits 0, a planted broken one exits 1",
    'The synthetic CargoQuote ARIS export (task-0119) equals its generator and both its BPMN dialects have no bpmnlint finding under the shipped rules',
    'The pre-load verdict read at the load (task-0064), rdflib, the example instance with its report; none without one, as the instance step above shows',
    'The gate as a command (task-0007) exits 0, 1 or 2 under the contract, and ratchets on the record',
    'The fail-closed hook (task-0099) against the live store, PROCEED lets the action through, BLOCKED, an unreachable store and a missing subject stop it',
    "The gate brings in S6's later version (task-0049), BLOCKED on four invalidated statements, then after re-verification exits 1 on the suspect derived output (task-0048)",
    "knowgov-trace (task-0051) on the example instance, a registered build of APP-0001 turns suspect after S6's change and check exits 1 naming it",
    "A register change invalidates (task-0122), the fixture's deprecated CAP-0001 and withdrawn REL-06001 stale the keys resting on them and S1's output suspect, exit 1; no state change, nothing; the staleness survives the round trip",
    'The pipeline wrappers (task-0052): the GitHub composite action, on the example instance, S6: setup',
    'The action: preload, clean, exit 0',
    "The action: gate on S1 as of 2027-08-08, a day after its reviews lapse, exit 1 (task-0089); with sarif (task-0116) its findings still go to code scanning, on a same-repository pull request only: on main they would be a fixture's standing alerts",
    'The action: gate on S6, exit 0',
    'The action: trace-register the reference code, exit 0',
    "The action: gate on S6's change, exit 1",
    "A code change in the instance's repository: an edit to the registered file",
    'The action: trace-check after the change, exit 1 naming APP-0001',
    "The action's two failing steps failed with exit 1, by their reports; then the GitLab include's script lines, run by a shell, the same command line",
    "The reports as annotations (task-0083): S6's change, from the action's two reports, as GitHub commands, code quality and SARIF",
    "A broken sequence diagram in the instance's repository (task-0106), after a story no subject names (task-0115)",
    "The action: preload on it, exit 1, its report and its annotations on the diagram's line",
    "The action's preload failed with exit 1, its report on the changed diagram alone, as a GitHub error on its line; the layout's problems beside it (task-0115)",
    'The capture path (task-0009), questionnaire, answers, the gate after, and nothing above proposed',
    "The review step (task-0037, decision-0002), S2' from BLOCKED to PROCEED by command, S4 settled whole, the six-month lapse",
    "One clock (task-0198), on rdflib, one --as-of gives one report under two KG_TODAY values; a person's approval lapses to proposed against it, a review-file approval with no verification lapses, what is dated after it is not counted, three_valued_answer marks the lapse",
    "Acts bound to content (task-0199), on rdflib, a ruling records what it ruled on, an edit after it is an act finding not an approval, a reordered table and renumbered answers move no act, stage 2 never moves one onto a successor, I4 and I9 refused",
    "Derived outputs bound to content (task-0199), on rdflib, the ledger records each used statement's value and digest, an edit and a reload under the same id reads suspect, the gate, MCP and trace read one rule",
    "One definition per concept (task-0201), on rdflib, one successor set for the gate, the stale finding, superseded_by and the bundle, disputed statements read, one owner and route, one uniqueness rule",
    "Attestations bound to their Versions (task-0221, decision-0019), on rdflib, the read rule at info, a listed Version attested, an edited unlisted one proposed and named, a digest of nothing refused",
    "The MCP server (task-0056) gives gate_cli's report for the same store, the record's three-valued answers, and writes nothing",
    "proposal_impact's branch mode (task-0132) through the CI template's step, doc-0017's worked example on a scratch branch of the public register, equal to the held overlay's report and the checkout unchanged",
    "A person's statement against the documents' (task-0038), on S2 a contradiction raises a conflict, an agreement corroborates and raises nothing",
    "The lighthouse protocol's public evidence (task-0069), CargoQuote from the example instance and the J-F kit (the subset on a pull request), every item agreeing with the record",
    "Route (c), a transcript read by a stub model (task-0041), gives inferred candidates on S2's empty keys only, listed in the questionnaire; no key, exit 2",
    "The store survives a round trip (task-0070), every CargoQuote scenario and J-F's (the subset on a pull request) through Turtle into a fresh store, the same gate reports and three-valued answers",
    "Stage 2 as a whole re-load (task-0197), on rdflib, a stage-2 gate equal to a fresh load of the later documents plus its stale and suspect findings, S6 and the H2, H4, I5, G5 plants on CargoQuote, I6 on J-F",
    'Store generations (task-0141.06, decision-0014) on a file-backed rdflib store: SNAP-01 to SNAP-09',
    "The outcomes, machine-readable, in the job's summary (task-0159)",
    'The outcome files kept as an artifact, 14 days, outcomes JSON only (task-0159)',
]
# Steps added after the split, each in one job: the same rule holds them
ADDED = ["Two subjects sharing a scenario id never answer each other's gates (task-0195): the held subject on a file-backed rdflib store",
         "pumllint's trace --features runs from the installed library (task-0224, for task-0217): the J-F kit's diagrams against its requirements and features, every requirement covered and verified",
         "One id per conflict (task-0223, decision-0020), every CargoQuote scenario loaded fresh twice, each conflict gap:conflict:<key>:<a>~<b>, ordered, S4's shown",
         "Pre-load findings as routed gaps (task-0216), on rdflib, the example instance's planted SEQ002 a lint gap with its owner and "
         "route and no level moved, held by the baseline, resolved by its owner, a slip in the re-lint delta, kept by the round trip",
         "The kit's claim (task-0214), on rdflib, the probe kit's five mappers read observed, inferred and intended into the basis, an inferred statement stays proposed and a ruling approving it is refused, an unknown claim is refused by the subject check"]
SHARED = OLD_STEPS[:3] + ["The outcomes, machine-readable, in the job's summary (task-0159)",
                          "The outcome files kept as an artifact, 14 days, outcomes JSON only (task-0159)"]


def _job(name: str) -> str:
    body = HARNESS.read_text(encoding="utf-8").split("\njobs:\n", 1)[1]
    parts = re.split(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", body)
    return dict(zip(parts[1::2], parts[2::2]))[name]


def _steps(block: str) -> list[str]:
    out = []
    for s in re.split(r"(?m)^      - ", block.split("    steps:\n", 1)[1])[1:]:
        m = re.search(r"(?m)^(?:        )?name: (.*)$", s)
        if m:
            out.append(m.group(1).strip().strip('"'))
        else:
            first = s.split("\n", 1)[0]
            out.append(re.sub(r"\s+#.*$", "", re.sub(r"^(uses|run): ", "", first)).strip()[:60])   # as YAML reads it
    return out


def test_every_step_of_the_old_job_runs_in_exactly_one_of_the_two():
    record, readers = _steps(_job("rdflib")), _steps(_job("rdflib-readers"))
    for s in SHARED:
        assert record.count(s) == 1 and readers.count(s) == 1, s
    own_r = [s for s in record if s not in SHARED]
    own_d = [s for s in readers if s not in SHARED]
    assert not set(own_r) & set(own_d), set(own_r) & set(own_d)
    assert sorted(own_r + own_d + SHARED) == sorted(OLD_STEPS + ADDED), sorted(set(OLD_STEPS + ADDED) ^ set(own_r + own_d + SHARED))
    # the record keeps the record: the suite, both subjects' record comparisons, the oracle, the round trip
    for must in ("The stdlib suite with the pins", "S1 to S7 on the in-memory store match the record",
                 "The J-F data-load subject, C and D1 to D5", "The J-F subject's oracle", "The store survives a round trip (task-0070)"):
        assert any(s.startswith(must) for s in own_r), must


def test_both_jobs_keep_the_old_jobs_environment_and_neither_needs_the_others_files():
    record, readers = _job("rdflib"), _job("rdflib-readers")
    assert "KG_CLOCK: pinned" in record and "KG_CLOCK: pinned" in readers
    top = HARNESS.read_text(encoding="utf-8").split("\njobs:\n", 1)[0]   # the subsets, one value for both jobs (task-0084)
    for var in ("KG_JF_SCENARIOS: ${{ github.event_name == 'pull_request' && 'C,D3' || '' }}",
                "KG_CQ_SCENARIOS: ${{ github.event_name == 'pull_request' && 'S1,S2,S6' || '' }}"):
        assert "\nenv:\n" in top and var in top and var not in record and var not in readers, var
    assert "outcomes/rdflib-checks.jsonl" in record and "outcomes/rdflib-readers-checks.jsonl" in readers
    assert "name: outcomes-rdflib\n" in record and "name: outcomes-rdflib-readers\n" in readers
    made = set(re.findall(r"runs/[\w.-]+", record))
    assert not made & set(re.findall(r"runs/[\w.-]+", readers)), "the readers would need a file the record's job makes"
    assert "security-events: write" not in record and "security-events: write" in readers
    assert "needs:" not in record and "needs:" not in readers   # parallel, each self-standing


def test_the_readers_job_makes_its_own_runs_folder_before_any_step_writes_into_it():
    """Before the split an earlier record step left runs/ behind; the readers' job now makes it first."""
    block = _job("rdflib-readers").split("    steps:\n", 1)[1]
    first_write = re.search(r"(?:tee|>|>>|-o|--output|--out)\s+runs/", block)
    made = block.find("mkdir -p runs")
    assert first_write and made != -1 and made < first_write.start(), "rdflib-readers writes into runs/ before making it"
