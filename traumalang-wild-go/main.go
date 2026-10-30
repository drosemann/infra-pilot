// Generate 100 x 1000-line traumalang wild features. Run explicitly by user.
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

var beats = []string{
	`TALK TO THE HAND "{name} phase {p:03d}: reconciling the {thing}"`,
	`PUT IT IN JIRA {name}-phase-{p:03d}`,
	`WE NEED TO TAKE THIS OFFLINE {name}_phase_{p:03d}`,
	`TALK TO THE HAND "{name} emitting metric {p}/1000"`,
	"THIS COULD HAVE BEEN AN EMAIL",
}

var things = []string{"solar-wind", "quantum-ticket", "moon-gate", "jira-aura", "flux-capacitor",
	"coffee-signal", "blameless-postmortem", "stargate-cache"}

func renderBeat(beat, name string, p int, thing string) string {
	s := strings.ReplaceAll(beat, "{name}", name)
	s = strings.ReplaceAll(s, "{p:03d}", fmt.Sprintf("%03d", p))
	s = strings.ReplaceAll(s, "{p}", fmt.Sprintf("%d", p))
	s = strings.ReplaceAll(s, "{thing}", thing)
	return s
}

func makeFile(name string) string {
	lines := []string{"IT'S SHOWTIME", "PUT IT IN JIRA " + name + " wild feature"}
	p := 0
	for len(lines) < 999 {
		p++
		thing := things[p%len(things)]
		beat := beats[p%len(beats)]
		lines = append(lines, renderBeat(beat, name, p, thing))
	}
	lines = append(lines, "YOU HAVE BEEN TERMINATED")
	if len(lines) != 1000 {
		panic(fmt.Sprintf("expected 1000 lines, got %d", len(lines)))
	}
	return strings.Join(lines, "\n") + "\n"
}

func main() {
	exe, err := os.Executable()
	if err != nil {
		fatal(err)
	}
	base := filepath.Dir(exe)
	if v := os.Getenv("TRAUMALANG_WILD_DIR"); v != "" {
		base = v
	} else if _, err := os.Stat(filepath.Join(base, "IDEAS.md")); err != nil {
		base = "."
	}
	raw, err := os.ReadFile(filepath.Join(base, "IDEAS.md"))
	if err != nil {
		fatal(err)
	}
	var names []string
	for _, l := range strings.Split(string(raw), "\n") {
		l = strings.TrimSpace(l)
		if l == "" || l[0] < '0' || l[0] > '9' {
			continue
		}
		if i := strings.Index(l, ". "); i >= 0 {
			l = l[i+2:]
		}
		names = append(names, l)
	}
	if len(names) != 100 {
		fatal(fmt.Errorf("expected 100 ideas, got %d", len(names)))
	}
	out := filepath.Join(base, "out")
	if err := os.MkdirAll(out, 0o755); err != nil {
		fatal(err)
	}
	for i, name := range names {
		if err := os.WriteFile(filepath.Join(out, fmt.Sprintf("%03d-%s.tl", i+1, name)), []byte(makeFile(name)), 0o644); err != nil {
			fatal(err)
		}
	}
	fmt.Printf("wrote %d files x 1000 lines to %s\n", len(names), out)
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, "error:", err)
	os.Exit(1)
}
