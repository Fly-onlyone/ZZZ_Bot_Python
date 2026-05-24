---
tags: [moc, backend, repositories]
---

# Backend / repositories — Map of Content

> Data persistence layer. An embedded SQLite database is the single runtime
> backend; the legacy JSON implementation remains for migration tooling only.

- [[DataStore]] — single-doc + multi-doc collection sets, schema + TTL purge, backup export/import
- [[DataRepository]] — abstract `IRepository<T>` interface; legacy JSON impl
- [[SQLite Connection]] — shared connection + process-wide lock

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[SQLite]]
- [[Settings Persistence Flow]]
- [[Backup Collection Registration Pattern]]
- [[Backup Endpoints]]
