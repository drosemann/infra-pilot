// tl2go translates traumalang-wild .tl files 1:1 to Go. Run explicitly by user.
//
// Usage: go run ./tl2go [tl-dir out-dir]
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func translateLine(line string) string {
	switch {
	case line == "IT'S SHOWTIME":
		return "package main\n\nimport \"fmt\"\n\nfunc main() {"
	case line == "YOU HAVE BEEN TERMINATED":
		return "}"
	case strings.HasPrefix(line, "PUT IT IN JIRA "):
		return "\t// " + line
	case strings.HasPrefix(line, "WE NEED TO TAKE THIS OFFLINE "):
		// Hyphenated names are not valid Go identifiers, so the
		// declaration survives as a comment instead of a func.
		return "\t// " + line
	case line == "THIS COULD HAVE BEEN AN EMAIL":
		return "\t// " + line
	case strings.HasPrefix(line, `TALK TO THE HAND "`) && strings.HasSuffix(line, `"`) && len(line) > len(`TALK TO THE HAND ""`):
		return "\tfmt.Println(\"" + line[len(`TALK TO THE HAND "`):len(line)-1] + "\")"
	default:
		return "\t// UNTRANSLATED: " + line
	}
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, "tl2go error:", err)
	os.Exit(1)
}

func main() {
	base := "."
	if v := os.Getenv("TRAUMALANG_WILD_DIR"); v != "" {
		base = v
	}
	inDir, outDir := filepath.Join(base, "..", "traumalang-wild", "out"), filepath.Join(base, "out-go")
	if len(os.Args) > 1 {
		inDir = os.Args[1]
	}
	if len(os.Args) > 2 {
		outDir = os.Args[2]
	}
	files, err := filepath.Glob(filepath.Join(inDir, "*.tl"))
	if err != nil {
		fatal(err)
	}
	if len(files) == 0 {
		fatal(fmt.Errorf("no .tl files in %s", inDir))
	}
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		fatal(err)
	}
	for _, f := range files {
		raw, err := os.ReadFile(f)
		if err != nil {
			fatal(err)
		}
		var out []string
		for _, line := range strings.Split(strings.TrimSuffix(string(raw), "\n"), "\n") {
			out = append(out, translateLine(line))
		}
		name := strings.TrimSuffix(filepath.Base(f), ".tl") + ".go"
		if err := os.WriteFile(filepath.Join(outDir, name), []byte(strings.Join(out, "\n")+"\n"), 0o644); err != nil {
			fatal(err)
		}
	}
	fmt.Printf("translated %d files to %s\n", len(files), outDir)
}
