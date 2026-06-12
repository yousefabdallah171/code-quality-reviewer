# Anti-Patterns Reference

## JavaScript / TypeScript

| Pattern | Why It's Bad | Fix |
|---------|-------------|-----|
| `any` type | Defeats TypeScript's purpose | Use specific types, `unknown`, or generics |
| `@ts-ignore` | Hides real bugs | Fix the type error properly |
| `useEffect` no deps | Runs every render | Add dependency array |
| `index` as React key | Causes re-render bugs with list mutations | Use stable unique IDs |
| `eval()` | Code injection risk | Use JSON.parse or safe alternatives |
| `innerHTML` / `dangerouslySetInnerHTML` | XSS vulnerability | Sanitize with DOMPurify |
| `readFileSync` in server | Blocks event loop | Use async `readFile` with `await` |
| `console.log` in production | Leaks info, clutters logs | Use structured logger (pino, winston) |
| `fetch` without error handling | Crashes on network errors | Wrap in try/catch, check `response.ok` |
| `cors()` with no config | Allows all origins | Specify allowed origins |
| Callback hell | Unreadable, error-prone | Use async/await |
| God components (500+ lines) | Untestable, hard to maintain | Split into smaller components |

## Python

| Pattern | Why It's Bad | Fix |
|---------|-------------|-----|
| Bare `except:` | Catches SystemExit, KeyboardInterrupt | Use `except Exception:` |
| Mutable default args `def f(x=[])` | Shared across calls | Use `None`, create inside function |
| `from module import *` | Namespace pollution | Import specific names |
| SQL string formatting | SQL injection | Use parameterized queries |
| `global` keyword | Hard to test, hidden state | Pass as parameters |
| `time.sleep()` in async code | Blocks the event loop | Use `asyncio.sleep()` |
| No type hints | Poor IDE support, unclear contracts | Add type annotations |
| Catching and silencing exceptions | Hides bugs | Log or re-raise |

## Go

| Pattern | Why It's Bad | Fix |
|---------|-------------|-----|
| `_, _ = someFunc()` | Discarded errors | Handle errors explicitly |
| Goroutine without recover | Panics crash program | Add defer/recover |
| `fmt.Print` in production | Not structured | Use log/slog |
| Shared mutable state without mutex | Race conditions | Use sync.Mutex or channels |
| Not closing HTTP response body | Resource leak | defer resp.Body.Close() |

## PHP

| Pattern | Why It's Bad | Fix |
|---------|-------------|-----|
| SQL string concatenation | SQL injection | Use PDO prepared statements |
| `extract()` | Creates vars from user input | Access array directly |
| `display_errors` on | Leaks server info | Disable in production |
| `md5()` for passwords | Cryptographically broken | Use `password_hash()` |
| `serialize()` user data | Object injection | Use `json_encode()` |

## Ruby

| Pattern | Why It's Bad | Fix |
|---------|-------------|-----|
| `params.permit!` | Mass assignment vulnerability | Whitelist: `permit(:name, :email)` |
| SQL string interpolation | SQL injection | Use `where('x = ?', val)` |
| `eval` with user input | Code injection | Use safe alternatives |

## General (All Languages)

| Pattern | Why It's Bad | Fix |
|---------|-------------|-----|
| Hardcoded secrets | Exposed in repo | Use environment variables |
| Magic numbers | Unclear intent | Named constants |
| Deep nesting (4+ levels) | Hard to read | Extract functions, early returns |
| God functions (100+ lines) | Hard to test | Split into smaller functions |
| Debug statements left in | Leaks info, clutters | Remove before commit |
| TODO/FIXME without tracking | Forgotten tech debt | Create issues to track |
| Copy-paste code | Maintenance burden | Extract shared function |
| No error messages | Hard to debug | Include context in errors |
