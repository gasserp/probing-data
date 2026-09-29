# probing-data

Accepted results from [probing](https://github.com/gasserp/probing) sensors:
the acceptance ledger, quarantine metadata, and the hourly to yearly rollups
behind the public dashboard at <https://gasserp.github.io/probing/>.

Every published value is a **self-reported suspected probe**. A signature
proves which registered sensor sent a report, not that the traffic was
malicious or that an address still belongs to the same party.

## Contents

| Path | What it holds |
|---|---|
| `registry/sources.json` | Registered sensors: source ID, epoch, key ID, public key, blob prefix, `kind` (`decoy` or `host`), and `enabled`. Changed only through a reviewed pull request. |
| `data/acceptance-ledger.json` | The replay authority: one payload hash per accepted batch, plus aggregate counters. |
| `data/quarantine.json` | Rejected batches, recorded only by filename, size, SHA-256, and reason code. |
| `data/rollups/{hourly,daily,monthly,yearly}.json` | The published aggregates the dashboard reads. |

The signed batches themselves are not stored here. Sensors upload them to
Azure Blob Storage, where they are kept for at most 30 days.

## How it updates

The `ingest` workflow runs hourly. It builds `probing-ingest` from the
`gasserp/probing` commit named in that repository's `deploy/VERSION` on `main`,
the same file the collector is deployed from, so the two stay in step. It then
downloads pending batches, accepts or quarantines each one, commits the
results, and deletes the accepted batches from storage.

Everything under `data/` is generated; do not edit it by hand. The full
contract is in
[`docs/data-repository.md`](https://github.com/gasserp/probing/blob/main/docs/data-repository.md).

## Takedown requests

To request removal or correction of a published record, open an issue with the
[takedown / revocation request](.github/ISSUE_TEMPLATE/revocation-request.md)
template.
