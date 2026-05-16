---
tags: [moc, backend, repositories]
---

# Backend / repositories — Map of Content

> Data persistence layer. MongoDB is the single runtime backend; legacy JSON
> implementation remains for migration only.

- [[MongoRepository]] — single-doc + multi-doc collection sets, TTL indexes, backup export/import
- [[DataRepository]] — abstract `IRepository<T>` interface; legacy JSON impl
- [[Mongo Connection]] — connection pool management

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[MongoDB]]
- [[Settings Persistence Flow]]
- [[Backup Collection Registration Pattern]]
- [[Backup Endpoints]]
