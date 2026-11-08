"""Model-like code the worker's isolation checks send as ``probe`` jobs (task-0203, doc-0030 F8): the code a
model could write to outlive its job (R4) or forge its answer (R7). ``tools/check_worker.py`` sends them to the
stack's worker; ``tests/test_worker_isolation.py`` to a worker loop on the test machine. No model is called:
each is fixture code, as hostile as a model's might be."""
from __future__ import annotations

import os
import secrets

DEPTH = 70   # the review's chain: the old reaper, one level a round for 50 rounds, left 21 of 70 alive


def marker() -> str:
    return "kg-probe-" + secrets.token_hex(6)


def chain(mark: str, depth: int = DEPTH) -> str:
    """A ``depth``-deep chain of processes, each in its own session (setsid), each sleeping, built whole
    before the job answers: each link reports through a pipe once its child, and so the whole chain below
    it, stands, so the job's ``built N`` follows the last fork, never races it. A fork that fails (a process
    bound reached) is reported by name as ``fork failed``, never as a short chain. The marker is in this
    code, so each link's command line carries it."""
    return f"""
import os, sys, time
MARK = {mark!r}
DEPTH = {int(depth)}

class Failed(Exception):
    \"\"\"A link below failed: its message is passed up as it is.\"\"\"

def link(d):
    \"\"\"Fork link d, which forks d - 1 below it; return once the whole chain below stands, or raise.\"\"\"
    r, w = os.pipe()
    pid = os.fork()
    if pid:
        os.close(w)
        got = b''
        while not got.endswith(b'\\n'):   # one line: every link below holds a copy of this pipe, so no EOF comes
            chunk = os.read(r, 256)
            if not chunk:
                break
            got += chunk
        os.close(r)
        got = got.strip()
        if got != b'ok':
            raise Failed(got.decode('utf-8', 'replace') or 'a link died before it answered')
        return
    os.close(r)
    try:
        os.setsid()
        null = os.open(os.devnull, os.O_RDWR)
        for fd in (0, 1, 2):
            os.dup2(null, fd)
        if d > 1:
            link(d - 1)
        os.write(w, b'ok\\n')
    except Failed as e:
        os.write(w, ('%s\\n' % e).encode())
        os._exit(1)
    except OSError as e:
        os.write(w, ('fork failed at depth %d: %s\\n' % (DEPTH - d + 1, e)).encode())
        os._exit(1)
    os.close(w)
    time.sleep(600)
    os._exit(0)

try:
    link(DEPTH)
except (Failed, OSError) as e:
    print(e if isinstance(e, Failed) else 'fork failed at depth 1: %s' % e)
    sys.exit(0)

n = 0
for p in os.listdir('/proc'):
    if p.isdigit() and int(p) != os.getpid():
        try:
            if MARK.encode() in open('/proc/' + p + '/cmdline', 'rb').read():
                n += 1
        except OSError:
            pass
print('built', n)
"""


def user_processes(uid: int) -> list[str]:
    """``uid``'s live processes as ``pid:starttime``, the start time telling a reused pid apart: the set a
    machine whose user owns more than the worker (a CI runner's) had before a job, for ``survivors``."""
    found = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/status") as f:
                owner = next(int(line.split()[1]) for line in f if line.startswith("Uid:"))
            with open(f"/proc/{d}/stat") as f:
                fields = f.read().rsplit(")", 1)[1].split()
        except (OSError, StopIteration, ValueError):
            continue
        if owner == uid and fields[0] not in ("Z", "X"):
            found.append(f"{d}:{fields[19]}")
    return found


def survivors(mark: str, before: list[str] | None = None) -> str:
    """The next job's view: how many processes carry ``mark``, and how many other processes of this user are
    alive, neither this job's own ancestry nor among ``before`` (``pid:starttime``, from ``user_processes``
    before the job; none by default, so in the worker's container, whose uid owns nothing else, every other
    process counts). Its first line is ``<marked> <others>``; then one ``OTHER pid ppid state cmdline`` line per
    other counted. The marker is split in this code, so this job's own command line does not carry it.

    task-0232: an other counts only when a second full scan about a second after the first also finds one,
    whichever pid it is (each scan a quarter-second window of scans, so a fast fork chain is not missed): a process caught exiting (its command line already empty, not yet a zombie) drops out,
    while a lingerer or a chain of short-lived forks is found by both. No command line is trusted, since a job
    writes its own: a process whose parent is outside the pid namespace (ppid 0, what ``docker exec`` brings in,
    the healthcheck among them) is not the job's, for every job process descends from the worker, the
    container's init, and an orphan reparents to it."""
    head, tail = mark[:8], mark[8:]
    return f"""
import os, time
MARK = ({head!r} + {tail!r}).encode()
BEFORE = set({sorted(before or [])!r})
me = os.getpid()
def stat(p):
    return open('/proc/%d/stat' % p).read().rsplit(')', 1)[1].split()
mine, p = set(), me
while p > 1:
    mine.add(p)
    try:
        p = int(stat(p)[1])
    except OSError:
        break
mine.add(1)
def scan():
    marked, found = 0, []
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        pid = int(d)
        try:
            cmd = open('/proc/%d/cmdline' % pid, 'rb').read()
            uid = next(int(l.split()[1]) for l in open('/proc/%d/status' % pid) if l.startswith('Uid:'))
            fields = stat(pid)
        except (OSError, StopIteration, ValueError):
            continue
        state, ppid = fields[0], int(fields[1])
        if state in ('Z', 'X'):
            continue
        if MARK in cmd:
            marked += 1
        elif uid == os.getuid() and pid not in mine and ppid != 0 and '%d:%s' % (pid, fields[19]) not in BEFORE:
            found.append((pid, ppid, state, cmd))
    return marked, found
def window():
    # scans for a quarter of a second, every 20 ms: a /proc listing is no snapshot, and a process that forks and
    # exits between the listing and its read leaves a child the listing never had, so one scan can miss a fast
    # fork chain; a process any scan of the window finds is counted, once
    marked, seen, end = 0, {{}}, time.monotonic() + 0.25
    while True:
        m, found = scan()
        marked = max(marked, m)
        for f in found:
            seen.setdefault(f[0], f)
        if time.monotonic() >= end:
            return marked, list(seen.values())
        time.sleep(0.02)
marked, others = window()
if others:   # counted only if a second window, a second later, still finds an other
    time.sleep(1.0)
    _, others = window()
print(marked, len(others))
for pid, ppid, state, cmd in others:
    print('OTHER', pid, ppid, state, ' '.join(cmd.replace(b'\\0', b' ').decode('utf-8', 'replace').split())[:120])   # one line each
"""


def forge(answer_mark: str) -> str:
    """The forge (R7): before its job's runner answers, open that runner's own output (its stdout, or any
    descriptor it holds) through /proc, hand it to a child in a session of its own, and have the child
    write a forged answer a second after this process has exited, while the worker still reads. The job's
    genuine output is ``answer_mark``; a forged answer carries ``FORGED``."""
    return f"""
import json, os, sys, time
runner = os.getppid()
fds = []
try:
    for name in os.listdir('/proc/%d/fd' % runner):
        try:
            fds.append(os.open('/proc/%d/fd/%s' % (runner, name), os.O_WRONLY | os.O_NONBLOCK))
        except OSError:
            pass
except OSError:
    pass
if os.fork() == 0:
    os.setsid()
    time.sleep(1.0)
    line = (json.dumps({{"exit": 0, "stdout": "FORGED", "stage": "ok"}}) + "\\n").encode()
    for fd in fds:
        try:
            os.write(fd, line)
        except OSError:
            pass
    os._exit(0)
print({answer_mark!r}, len(fds))
"""


def fork_chain(mark: str, life_ms: float = 1.0, seconds: float = 20.0) -> str:
    """The reaper's adversary (task-0233): a double fork into a session of its own, its pipes released so the
    job answers while it runs on, then a chain whose every process lives ``life_ms``, forks the next, takes a
    new session and exits, for ``seconds``. No pid lives long; the chain does, unless the worker ends it."""
    return f"""
import os, time
MARK = {mark!r}
if os.fork() == 0:
    os.setsid()
    null = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(null, fd)
    if os.fork() == 0:
        end = time.time() + {float(seconds)}
        while time.time() < end:
            try:
                if os.fork():
                    os._exit(0)
            except OSError:
                time.sleep(0.001)
                continue
            os.setsid()
            time.sleep({float(life_ms) / 1000})
        os._exit(0)
    os._exit(0)
time.sleep(0.3)
print('started')
"""


def ns_quiet(mark: str, seconds: float = 1.0, windows: int = 2) -> str:
    """The next job's witness (task-0233), in the worker's own pid namespace:
    ``<allocated per window...> <marked> <init>``, the pids the namespace allocated in each of ``windows``
    consecutive windows of ``seconds`` (a chain still running forks hundreds in every one), the processes carrying
    ``mark`` seen over them all, and whether the worker is the namespace's init (its pid 1, where its reaper
    confirms quiet by this same counter). The marker is split in this code, so this job's own command line does
    not carry it."""
    head, tail = mark[:8], mark[8:]
    return f"""
import os, time
MARK = ({head!r} + {tail!r}).encode()
def counter():
    return int(open('/proc/sys/kernel/ns_last_pid').read())
def marked():
    n = 0
    for d in os.listdir('/proc'):
        if d.isdigit():
            try:
                n += MARK in open('/proc/%s/cmdline' % d, 'rb').read()
            except OSError:
                pass
    return n
init = b'worker.py' in open('/proc/1/cmdline', 'rb').read()   # the worker is this namespace's pid 1
allocated, most = [], 0
for _ in range({int(windows)}):
    a, end = counter(), time.monotonic() + {float(seconds)}
    while time.monotonic() < end:
        most = max(most, marked())
        time.sleep(0.005)
    allocated.append(counter() - a)
print(*allocated, most, int(init))
"""
