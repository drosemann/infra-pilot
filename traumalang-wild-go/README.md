# traumalang-wild-go — 100 wild features (Go port)

1:1 port of [../traumalang-wild](../traumalang-wild) (`generate.py` → `main.go`).
No dependencies, stdlib only. Same behavior: reads `IDEAS.md`, writes
`out/001-*.tl` … `100-*.tl`, each exactly 1000 lines, starting with
`IT'S SHOWTIME`, ending with `YOU HAVE BEEN TERMINATED`.

## Use

```
cd traumalang-wild-go
go run .
```

Override the folder (instead of the executable dir) with:

```
TRAUMALANG_WILD_DIR=. go run .
```

## .tl → .go translator

`tl2go/` translates all 100 `.tl` files 1:1 to Go (`out-go/*.go`).
Line mapping (each file is `package main`, statements in `func main`):

| `.tl` | `.go` |
| --- | --- |
| `IT'S SHOWTIME` / `YOU HAVE BEEN TERMINATED` | program frame (`package main`, `import "fmt"`, `func main() {` / `}`) |
| `TALK TO THE HAND "…"` | `fmt.Println("…")` |
| `PUT IT IN JIRA …` | `// PUT IT IN JIRA …` |
| `WE NEED TO TAKE THIS OFFLINE …` | `// …` (names contain hyphens, invalid as Go identifiers) |
| `THIS COULD HAVE BEEN AN EMAIL` | `// THIS COULD HAVE BEEN AN EMAIL` |
| anything else | `// UNTRANSLATED: …` (never silently emitted as equivalent) |

```
cd traumalang-wild-go
go run ./tl2go [tl-dir out-dir]
```

Ohne Go-Toolchain geht es auch per PowerShell (gleiches Mapping):

```
./traumalang-wild-go/tl2go.ps1
```

Each `.go` file builds standalone (`go run out-go/003-deploy-to-the-moon.go`);
they share `package main`/`func main`, so `out-go/` itself is not one package.
