# ⚡ Kosha
A lightweight, in-memory key-value store built from scratch in Python. Supports namespaces, TTL-based key expiry, and a TCP interface for client communication.

> Creating this project to better understand Redis and TCP internals.

---

## Features

- **In-memory hashmap** with custom hash function and chaining for collision resolution
- **TTL (Time-To-Live)** on every key with both lazy deletion (on read) and active expiry sweeping
- **Namespaces** — isolated key spaces within the same server instance
- **TCP server** — clients connect over TCP and send plain-text commands
- **Simple text protocol** — human-readable, testable with `nc` (netcat)

---

## Architecture

The server is split into 4 layers, each with a single responsibility:

```
Client (telnet / nc / custom)
  │
  ▼
┌─────────────────────────────────┐
│  Layer 1: TCP Server            │
│  Accept connections, read/write │
│  bytes, spawn client handlers   │
├─────────────────────────────────┤
│  Layer 2: Protocol Parser       │
│  Raw text ↔ Command objects     │
│  "SET k v EX 30\n" → Command() │
├─────────────────────────────────┤
│  Layer 3: Command Router        │
│  Route commands to store methods│
│  Manage per-connection state    │
├─────────────────────────────────┤
│  Layer 4: KeyValueStore         │
│  Hashmaps, namespaces, TTL      │
│  Pure data structure, no I/O    │
└─────────────────────────────────┘
```

**Key design rule:** Layer 4 (KeyValueStore) has zero knowledge of TCP. It's a pure data structure that can be used without a network.

### Request Flow

```

1. Client sends         →  "SET user:1 john EX 30\n"
2. TCP Server receives  →  raw bytes
3. Protocol Parser      →  Command(action="SET", key="user:1", value="john", ttl=30)
4. Command Router       →  store.get_namespace("default").put("user:1", "john", ttl=30)
5. Command Router       →  Response(data="OK")
6. Protocol Parser      →  "OK\n"
7. TCP Server sends     →  raw bytes back to client
```

---

## Project Structure

```

kvstore/
├── main.py            # Entry point — starts the server, wires everything
├── tcp.py          # Layer 1: TCP server (accept, read, write)
├── parser.py        # Layer 2: parse_command() + format_response()
├── handler.py         # Layer 3: route command → call store method
├── kv_store.py           # Layer 4: KeyValueStore + Hashmap
└── README.md

```

---

## Protocol Specification

### Command Format

```

COMMAND arg1 arg2 ... \n

```

Each command is a single line terminated by `\n`. Arguments are space-separated.

### Supported Commands

| Command | Syntax | Response | Description |
|---------|--------|----------|-------------|
| `SET`   | `SET key value [EX seconds]` | `OK` | Store a key-value pair. Optional TTL in seconds. |
| `GET`   | `GET key` | `value` or `(nil)` | Retrieve value by key. Returns `(nil)` if not found or expired. |
| `DEL`   | `DEL key` | `OK` or `(nil)` | Delete a key. Returns `(nil)` if key doesn't exist. |
| `TTL`   | `TTL key` | `seconds`, `-1`, or `-2` | Remaining TTL. `-1` = no expiry, `-2` = key doesn't exist. |
| `USE`   | `USE namespace` | `OK` | Switch to a namespace. Creates it if it doesn't exist. |
| `KEYS`  | `KEYS` | `key1 key2 ...` | List all keys in the current namespace. |
| `PING`  | `PING` | `PONG` | Health check. |
| `QUIT`  | `QUIT` | *(closes connection)* | Disconnect from server. |

### Response Format

```

OK\n                   # Success
value\n                # Value returned
(nil)\n                # Key not found or expired
ERROR message\n        # Something went wrong

```

### Example Session

```
> PING
PONG
> SET name john
OK
> SET session abc123 EX 300
OK
> GET name
john
> TTL session
298
> USE cache
OK
> GET name
(nil)
> USE default
OK
> GET name
john
> DEL name
OK
> GET name
(nil)
> QUIT
```

---

## Current Implementation Status

### ✅ Completed

- [x] Custom hashmap with chaining (collision handling)
- [x] `PUT` / `GET` / `DELETE` operations
- [x] TTL support with configurable default and per-key expiry
- [x] Lazy expiry — expired keys are cleaned up on `GET`
- [x] Active expiry — background sweep deletes expired keys periodically
- [x] Namespace support — isolated key spaces via `KeyValueStore` wrapper
### 🔨 In Progress
- [ ] TCP server (Layer 1)
- [ ] Protocol parser (Layer 2)
- [ ] Command router (Layer 3)
### 📋 Planned
- [ ] Handle multiple concurrent clients
- [ ] Persistence — append-only log (AOF) for crash recovery
- [ ] `KEYS` command
- [ ] `TTL` command
- [ ] Graceful server shutdown
- [ ] Rewrite in Go with raw TCP and goroutines

---

## Usage

### Running the Server

```bash

python main.py
# Server listening on localhost:7000

```

### Connecting (using netcat)

```bash

nc localhost 7000

```

Then type commands as shown in the protocol section above.

---

## Design Decisions

### Why a custom hashmap instead of Python's `dict`?

To understand how hash tables work internally — hash functions, bucket arrays, collision resolution via chaining. Python's `dict` is a highly optimized C implementation. Building one from scratch teaches the fundamentals.

### Why raw TCP instead of HTTP/REST?

KV stores are high-throughput, low-latency systems. HTTP adds overhead (headers, content negotiation, JSON serialization) that doesn't serve the use case. Redis, Memcached, and etcd all use TCP with custom protocols for this reason.

### Why namespaces?

Logical isolation of keys without running multiple server instances. Similar to Redis's `SELECT` database feature. Implementation is simple — a dictionary of hashmaps — but the abstraction enables multi-tenant use cases.

### Why lazy + active expiry?

- **Lazy** (check on read): Cheap, O(1) per GET. But keys that are never read again will leak memory.
- **Active** (background sweep): Catches keys that lazy expiry misses. Runs periodically, cleans up unreferenced expired keys.
Both together give correctness (lazy) + memory efficiency (active). This is how Redis does it.

---

## Persistence Plan (Future)

**Approach: Append-Only File (AOF)**

```cmd

1. Every write command (SET, DEL) gets appended to a log file:
     SET user:1 john EX 30
     SET session abc123 EX 300
     DEL user:1
2. On server startup, replay the log to rebuild in-memory state.
3. Periodic compaction: rewrite the log, removing redundant entries.
```

SQLite may be used later for periodic snapshots as an alternative/complement to AOF.

---

## Tech Stack

- **Language:** Python 3.11+
- **Networking:** `asyncio` + raw TCP sockets
- **Concurrency:** `asyncio` event loop + `ThreadPoolExecutor` for background sweeps
- **Persistence:** Append-only log file (planned)
- **Future rewrite:** Go (for goroutines, `net` package, and raw TCP)

---

## What This Project Teaches

| Area | What I'm Learning |
|------|-------------------|

| Data Structures | Hash tables, chaining, bucket arrays |
| Networking | TCP sockets, client-server model, protocol design |
| Concurrency | Async I/O, thread pools, handling multiple clients |
| Systems Design | Layered architecture, separation of concerns |
| Persistence | Write-ahead logs, crash recovery, durability vs performance |
| Protocol Design | Framing, parsing, request-response patterns |

---
