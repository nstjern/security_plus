# Contracts

The source of truth for how the client, the API, and the database talk to each other.

Unlike a hand-maintained document, `openapi.json` is generated from the running application:

```bash
cd backend && python -m app.export_openapi ../contracts/openapi.json
```

CI regenerates it and fails if the committed copy has drifted, so the contract can never
quietly disagree with the code. Once the frontend exists, its TypeScript types are generated
from this same file, which makes a breaking API change a compile error in the browser.

## Contents

| Path | What it holds |
|---|---|
| `openapi.json` | Generated API contract: endpoints, schemas, status codes |
| `adr/` | Architecture decision records — why the stack looks the way it does |

## Architecture decision records

An ADR captures one decision, the alternatives considered, and the consequences accepted.
They are numbered, immutable once merged, and superseded rather than edited.

Implementation does not belong here. This directory records *what* the system does and *why*,
separately from *how*.
