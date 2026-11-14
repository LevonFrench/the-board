# Creator Docs helper

Load only when retrieving Roblox Creator Docs with the local helper. The [Roblox contract](roblox.md) still applies.

The stdlib [helper](../scripts/creator_docs.py) reads the local corpus at $CREATOR_DOCS_DIR without building an index or changing sparse checkout. Git is optional; all Git transports, credential helpers, optional locks and lazy fetch are disabled. The selected root gets a command-local safe.directory setting for sandbox ownership differences; global Git configuration is not changed. Retrieval makes no service requests, installs, licence checks or credential reads.

```powershell
python -B 'scripts/creator_docs.py' search 'remote' --scope 'content/en-us/scripting' --limit 5 --scan-limit 100
python -B 'scripts/creator_docs.py' lookup 'content/en-us/reference/engine/classes/RemoteEvent.yaml' --member 'RemoteEvent:FireServer'
python -B 'scripts/creator_docs.py' lookup 'content/en-us/cloud-services/data-stores/player-data-purchasing.md'
```

## Behaviour

- `--root '<absolute corpus path>'` before the subcommand selects another local snapshot. Input paths are repository-relative identifiers under `content/en-us`; displayed source paths are absolute.
- Lookup reports HEAD, observed time, whole-file SHA-256, source kind and availability: `materialized`, `git-object`, `unavailable-locally` or `unknown`. A working file may differ from HEAD; `matches_head_blob` compares exact bytes where supported. HEAD and API documentation are not the installed Studio version.
- Raw Markdown/YAML/JSON is returned unchanged after UTF-8 decoding. Exact generated-YAML member selection keeps the complete member block plus the entity prelude (tags, deprecation, security, capabilities, signatures as present). It does not interpret YAML; omit `--member` for complete source or an unfamiliar layout. The hash always covers the complete original file. Sources over 2 MiB are neither partially returned nor hashed.
- Search enumerates the local Git tree and a bounded working-tree walk, reads at most the requested number of title headers and returns at most 20 candidates. It never claims full-text or member coverage. A missing match or unavailable object does not prove an API is absent. Narrow the scope before raising limits.
- Explicit lookup is the availability/hash receipt; search candidates are navigation hints. Follow includes and API links explicitly; retrieval never expands dependencies or refreshes the corpus.

## Source contracts

Available at revision `9f840b170b3e472c705e035126b45e3e050daed2` on 2026-10-04; recheck for the current assignment. The player-data guide describes its own example as unproven at scale.

- [Data-store best practices](https://github.com/Roblox/creator-docs/blob/main/content/en-us/cloud-services/data-stores/best-practices.md)
- [Player data and purchasing](https://github.com/Roblox/creator-docs/blob/main/content/en-us/cloud-services/data-stores/player-data-purchasing.md)
- [Developer products](https://github.com/Roblox/creator-docs/blob/main/content/en-us/production/monetization/developer-products.md)
- [Client/server boundary](https://github.com/Roblox/creator-docs/blob/main/content/en-us/scripting/security/client-server-boundary.md)

