"""Generate 100 x 1000-line traumalang wild features. Run explicitly by user."""
from pathlib import Path

OUT = Path(__file__).parent / "out"

IDEAS = [l.strip() for l in (Path(__file__).parent / "IDEAS.md").read_text().splitlines()
         if l.strip() and l.strip()[0].isdigit()]
NAMES = [i.split(". ", 1)[1] if ". " in i else i for i in IDEAS]
assert len(NAMES) == 100, f"expected 100 ideas, got {len(NAMES)}"

BEATS = [
    'TALK TO THE HAND "{name} phase {p:03d}: reconciling the {thing}"',
    'PUT IT IN JIRA {name}-phase-{p:03d}',
    'WE NEED TO TAKE THIS OFFLINE {name}_phase_{p:03d}',
    'TALK TO THE HAND "{name} emitting metric {p}/1000"',
    "THIS COULD HAVE BEEN AN EMAIL",
]

THINGS = ["solar-wind", "quantum-ticket", "moon-gate", "jira-aura", "flux-capacitor",
          "coffee-signal", "blameless-postmortem", "stargate-cache"]


def make_file(name: str) -> str:
    lines = ["IT'S SHOWTIME", f'PUT IT IN JIRA {name} wild feature']
    p = 0
    while len(lines) < 999:
        p += 1
        thing = THINGS[p % len(THINGS)]
        beat = BEATS[p % len(BEATS)]
        lines.append(beat.format(name=name, p=p, thing=thing))
    lines.append("YOU HAVE BEEN TERMINATED")
    assert len(lines) == 1000
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for i, name in enumerate(NAMES, 1):
        (OUT / f"{i:03d}-{name}.tl").write_text(make_file(name))
    print(f"wrote {len(NAMES)} files x 1000 lines to {OUT}")


if __name__ == "__main__":
    main()
