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
| `registry/sources.json` | Registered sensors: source ID, epoch, key ID, public key, blob prefix, `kind` (`decoy` or `host`), the `github_repository` a contributor's sensor publishes to, and `enabled`. Changed only through a reviewed pull request. |
| `data/acceptance-ledger.json` | The replay authority: one payload hash per accepted batch, plus aggregate counters. |
| `data/quarantine.json` | Rejected batches, recorded only by filename, size, SHA-256, and reason code. |
| `data/rollups/{hourly,daily,monthly,yearly}.json` | The published aggregates the dashboard reads. |

The signed batches themselves are not stored here. Contributors' sensors
publish them to the contributors' own public GitHub repositories. The
maintainer's sensors upload them to Azure Blob Storage, where they are kept for
at most 30 days.

## Contributing a sensor

Run a sensor, publish its batches to a public repository you own, and open a
pull request that adds its registry entry. Nothing else is needed from the
maintainer. The step-by-step guide is
[`docs/raspberry-pi.md`](https://github.com/gasserp/probing/blob/main/docs/raspberry-pi.md).

## How it updates

The `ingest` workflow runs hourly. It builds `probing-ingest` and
`probing-fetch` from the `gasserp/probing` commit named in that repository's
`deploy/VERSION` on `main`, the same file the collector is deployed from, so
the two stay in step. It then collects pending batches from two places:

- the public GitHub repository each contributor's sensor publishes to, named
  by `github_repository` in the registry;
- the reference deployment's Azure Blob container, for the maintainer's own
  sensors.

It accepts or quarantines each batch, commits the results, and deletes
accepted batches from the Azure container. Contributor repositories are never
modified.

Everything under `data/` is generated; do not edit it by hand. The full
contract is in
[`docs/data-repository.md`](https://github.com/gasserp/probing/blob/main/docs/data-repository.md).

## Takedown requests

To request removal or correction of a published record, open an issue with the
[takedown / revocation request](.github/ISSUE_TEMPLATE/revocation-request.md)
template.
