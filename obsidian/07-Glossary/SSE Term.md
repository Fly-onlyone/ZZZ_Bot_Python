---
tags: [glossary]
---

# SSE

> Server-Sent Events — a one-way HTTP streaming protocol where the server pushes text-formatted events to the browser over a single long-lived connection.

## How it works
Browsers consume SSE via `new EventSource(url)`. The server keeps the connection open and writes `data: <json>\n\n` lines whenever it has something to say. ZZZ Bot exposes an SSE endpoint that streams events from the in-process [[Event Bus]]; the React [[useTaskEvents]] hook subscribes and pushes deltas into TanStack Query. SSE is simpler than WebSocket because it is unidirectional and survives proxies that allow HTTP/1.1 chunked transfer.

## See also
- [[_index]]
- [[SSE Event Bus Pattern]]
- [[Event Bus]]
