"""The browser console and the Python scorer must agree on the rules.

The rules exist twice now, once in `outbabyout.py` and once in the `rules`
script block of `play.html`. Two implementations that look consistent and are
not is the same class of bug as a false zero: the console would happily record
a match the scorer then refuses to score, and nobody would find out until the
log came back.

So this runs the real JavaScript, not a copy of it. It pulls the block straight
out of the page, runs it in node, and checks every answer against what
`play()` does with the same situation.

    py -3 -m pytest tests/ -q          needs node on PATH
"""

import io
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import outbabyout as obo


def have_node():
    try:
        subprocess.run(["node", "-v"], capture_output=True, timeout=10)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not have_node(), reason="node is not on PATH")


def js_rules(tmp_path):
    """The rules block, lifted verbatim out of play.html.

    Verbatim matters. A copy of the rules in the test would agree with itself
    forever and prove nothing.
    """
    page = io.open(os.path.join(ROOT, "play.html"), encoding="utf-8").read()
    m = re.search(r'<script id="rules">(.*?)</script>', page, re.S)
    assert m, "play.html has no rules block - did someone inline it again?"
    body = m.group(1)
    # Look at the code, not the prose. The comment in that block says the words
    # "document" and "window" precisely to tell the next person not to use them,
    # and the first version of this guard failed on its own explanation.
    code = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    assert "document." not in code and "window." not in code, \
        "the rules block touched the DOM; it has to stay pure to be testable"
    path = tmp_path / "rules.js"
    io.open(str(path), "w", encoding="utf-8", newline="\n").write(body)
    return str(path)


def ask_js(rules_path, side, frozen, actor, target):
    """What the page would do, from the page's own code."""
    script = (
        "const r = require(%s);\n"
        "const out = r.verdict(%s, %s, %s, %s);\n"
        "process.stdout.write(JSON.stringify(out));\n"
        % (json.dumps(rules_path.replace("\\", "/")), json.dumps(side),
           json.dumps(frozen), json.dumps(actor), json.dumps(target))
    )
    done = subprocess.run(["node", "-e", script], capture_output=True,
                          timeout=30, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def ask_python(teams, done_events, actor, mark, target):
    """What the scorer would do with the same move appended."""
    events = list(done_events) + [{"at": 600, "actor": actor, "mark": mark,
                                   "target": target, "line": 99}]
    try:
        obo.play(1200, teams, events)
        return True, ""
    except obo.Bad as exc:
        return False, str(exc)


TEAMS = {"RED": ["a", "b"], "BLUE": ["x", "y"]}
SIDE = {"a": "RED", "b": "RED", "x": "BLUE", "y": "BLUE"}
# One frozen player on each side to aim at. The first version of this fixture
# had x freezing someone after x had already been frozen, and the scorer threw
# it out - which is the engine doing its job to a test that was wrong.
PRIOR = [{"at": 60, "actor": "a", "mark": ">", "target": "x", "line": 1},
         {"at": 90, "actor": "y", "mark": ">", "target": "b", "line": 2}]
FROZEN = {"x": True, "b": True}

# (actor, target, what it should be). Written from the rules, not from either
# implementation, so it can catch both of them being wrong the same way.
CASES = [
    ("a", "y", ">"),      # enemy, standing: a catch
    ("a", "b", "+"),      # teammate, frozen: a rescue
    ("a", "x", None),     # enemy, already frozen
    ("y", "x", "+"),      # their teammate, frozen: their rescue
    ("y", "a", ">"),      # the other way round
    ("b", "y", None),     # actor is frozen
    ("b", "a", None),     # actor is frozen, aiming at a teammate
    ("a", "a", None),     # acting on yourself
    ("a", "zz", None),    # not on any team
    ("zz", "a", None),    # not on any team, acting
]


@pytest.mark.parametrize("actor,target,expected", CASES)
def test_console_and_scorer_agree(tmp_path, actor, target, expected):
    rules = js_rules(tmp_path)
    js = ask_js(rules, SIDE, FROZEN, actor, target)

    assert js["ok"] == (expected is not None), (
        "the console would %s %s -> %s; the rules say %s"
        % ("allow" if js["ok"] else "refuse", actor, target,
           "allow" if expected else "refuse"))

    if expected is None:
        assert js["why"].strip(), "a refusal with no reason is not a refusal"
        # Whatever the console refuses, the scorer must also refuse. Try it
        # both ways round, because the console never even picks a mark.
        for mark in (">", "+"):
            ok, _ = ask_python(TEAMS, PRIOR, actor, mark, target)
            assert not ok, ("the console refuses %s %s %s but the scorer would "
                            "accept it" % (actor, mark, target))
        return

    assert js["mark"] == expected
    ok, why = ask_python(TEAMS, PRIOR, actor, js["mark"], target)
    assert ok, ("the console would record %s %s %s and the scorer refuses it: %s"
                % (actor, js["mark"], target, why))


def test_a_console_match_survives_the_scorer(tmp_path):
    """Play a whole match through the JavaScript, then score it in Python.

    This is the one that matters: the console writes the log, and the log has
    to be readable by the thing that reads logs.
    """
    rules = js_rules(tmp_path)
    frozen, events, clock = {}, [], 0
    script = [("a", "y"), ("x", "y"), ("y", "b"), ("a", "b"),
              ("b", "x"), ("y", "x"), ("a", "x"), ("b", "y")]

    for actor, target in script:
        clock += 70
        js = ask_js(rules, SIDE, frozen, actor, target)
        if not js["ok"]:
            continue                       # the console would have refused it
        events.append("%d:%02d  %s %s %s"
                      % (clock // 60, clock % 60, actor, js["mark"], target))
        if js["mark"] == ">":
            frozen[target] = True
        else:
            frozen.pop(target, None)

    assert len(events) >= 5, "the script never produced a usable match"

    log = "\n".join(["# crosscheck", "LENGTH 20:00", "",
                     "RED   a, b", "BLUE  x, y", ""] + events)
    length, teams, parsed = obo.parse(log)
    left, tree = obo.play(length, teams, parsed)

    assert len(tree) == len(events)
    # And the frozen set the two arrived at independently must be the same one.
    assert left == set(k for k, v in frozen.items() if v)


def test_the_crosscheck_can_fail(tmp_path):
    """Proof the test bites: break the JS rule and watch it get caught."""
    page = io.open(os.path.join(ROOT, "play.html"), encoding="utf-8").read()
    body = re.search(r'<script id="rules">(.*?)</script>', page, re.S).group(1)
    broken = body.replace("if (frozen[actor])", "if (false && frozen[actor])")
    assert broken != body, "the frozen-actor guard is not where the test thinks"

    path = tmp_path / "broken.js"
    io.open(str(path), "w", encoding="utf-8", newline="\n").write(broken)

    js = ask_js(str(path), SIDE, FROZEN, "b", "y")   # b is frozen
    assert js["ok"], "sanity: the broken build should wrongly allow this"
    ok, _ = ask_python(TEAMS, PRIOR, "b", js["mark"], "y")
    assert not ok, "the scorer should still refuse it, which is the disagreement"
