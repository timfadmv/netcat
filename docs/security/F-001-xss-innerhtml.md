# F-001: HTML injection through `innerHTML` (CWE-79)

| | |
|---|---|
| Status | Fixed and verified |
| Component | `static/script.js` (all result and session views) |
| CWE | CWE-79 Improper Neutralization of Input During Web Page Generation |
| Severity | Low (CVSS 3.1 base 4.2 Medium, adjusted, see Severity) |
| Found in | `baseline-v0.1` |

## Description

The web interface builds its result and session views with `innerHTML` and puts text into the markup
without escaping it. The text comes from the user (host name, port) and from the API (the error and
success messages repeat the host name). 24 places write HTML:

| Places | Count |
|---|---|
| contain such data **without escaping** (for example `` resultDiv.innerHTML = `...${data.error}...` `` after a failed connection) | 17 |
| escape the data with `escapeHtml()` (the message typed into a session) | 2 |
| constant markup (spinner, clearing a box) | 5 |

## Reproduction (against `baseline-v0.1`, on 127.0.0.1)

1. Start the application: `NETCAT_PORT=5055 uv run python app.py` and open http://127.0.0.1:5055/.
2. On the *TCP Connect* tab enter this host name, port `80`, timeout `1`, and press *Connect*:

   ```
   <h1 id="pwn">PWNED</h1><img id="img1" src=x onerror="window.__xss=1">
   ```

3. The API answers `Cannot resolve host: <h1 id="pwn">PWNED</h1>...` and the page puts it into the
   result box as markup.

Observed result, checked in the browser:

| Check | Result |
|---|---|
| `<h1 id="pwn">` exists in the result box | yes |
| `<img id="img1">` exists in the result box | yes |
| the `onerror` handler ran (`window.__xss`) | **no**, blocked by the Content-Security-Policy |
| visible text | `Cannot resolve host:` followed by `PWNED` as a heading |

The attacker controls the markup of the page, but not its scripts.

## Root cause

Untrusted text is concatenated into an HTML string and parsed as HTML (`innerHTML`). The data is never
treated as text. Escaping each value by hand (`escapeHtml`) fails open: a single place that forgets it
is vulnerable, and 17 of the 19 places with data forgot it.

## Severity

CVSS 3.1: `AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:L/A:N` = 4.2 (Medium).

Adjusted to **Low** for the context of this application:

- the injected text is the one the user typed into the form; there is no URL parameter, stored data or
  other channel through which a third party can put text into the page
- another site cannot trigger the request: the API accepts only `application/json`, which a cross-site
  request cannot send without a CORS preflight, and the response is not readable by that site
- the Content-Security-Policy (`script-src 'self'`) blocks script execution, so the impact is limited to
  changing what the page shows (content spoofing)

The preconditions change if the application starts to display data from a remote party (for example the
data received on a connection): then the same flaw would be exploitable by that party.

## Fix

The views are built from DOM nodes instead of HTML strings (`fix(security)` commit of this finding). A
string given to `append()` becomes a text node, so text cannot turn into markup, whatever it contains.
This removes the cause (text parsed as HTML), not one symptom: no value needs to be escaped, so no value
can be forgotten.

- helpers `node()`, `showResult()`, `showError()`, `appendOutput()` and one `showSession()` for both the
  connect and the listen session (it replaces two copies of an HTML template)
- the scan result is built from nodes as well
- `escapeHtml()` is removed

## Verification

| Check | Before | After |
|---|---|---|
| `tests/test_xss.py` | fails: 24 `innerHTML` lines, no DOM nodes | passes |
| proof of concept in the browser: `<h1 id="pwn">` in the result box | present | **absent** |
| proof of concept: `<img id="img1">` in the result box | present | **absent** |
| the markup is visible as literal text | no (shown as a heading) | **yes** |
| `onerror` handler executed | no (blocked by CSP) | no (the element is not created) |
| connect, send, close, listen timeout, port scan | work | work |
| text sent with markup (`hello <b id="bold">x</b>`) | shown as text | arrives unchanged at the target, shown as text |
| whole suite and ruff | 40 passed | 48 passed, ruff clean |

## Residual risk

- The regression test is static: it forbids the HTML-parsing APIs but does not run the script. A new
  sink of another kind (for example assigning a user value to a `href` or `src` attribute) would not be
  caught by it.
- The Content-Security-Policy stays as the second line of defence; it was not needed to stop this
  injection any more, but it also covers mistakes in future code.
- The API still reflects whatever host name it receives in its messages. That is harmless for a client
  that treats it as text, and the validation of the input is a separate finding.
- If the application starts to display data received from a remote party, it must go through the same
  helpers.
