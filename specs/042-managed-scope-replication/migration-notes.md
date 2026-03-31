# Migration Notes: Managed Scope Replication (Tranche A)

**Feature**: `042-managed-scope-replication`
**Target Audience**: Operators of existing Aegis local-first databases

## What Changed

The Aegis engine has evolved to support a **multi-node/replica identity model**. To enable safe distributed synchronization without silent data loss, every Aegis database now has a unique `Node Identity`. 

The SQLite database schema has been expanded to support:
1.  **`node_identities`**: Records the identity of the local device and any remote devices it syncs with.
2.  **`replication_audit_log`**: An immutable ledger of all inbound synchronization mutations, ensuring replay-safety.
3.  **`origin_node_id` in `memories`**: Every memory now strictly tracks which node created or last modified it.
4.  **`reconcile_required` status**: A new valid status for `memories`. Instead of silently overwriting concurrent edits during sync, conflicting mutations are now flagged for manual operator review.

## How to Migrate

A migration script is provided to safely transition existing local-only `memory_aegis.db` files to the new schema without data loss.

### Step 1: Backup your database
Always back up your database before running schema migrations.
```bash
cp memory_aegis.db memory_aegis.db.backup
```

### Step 2: Run the Migration Script
Run the provided Python script located in the `scripts/` directory:
```bash
python scripts/migrate_042_managed_scope_replication.py /path/to/your/memory_aegis.db
```

### Step 3: What to Expect
- The script uses SQLite's temporary table swapping to safely update constraints.
- Existing memories will have their `origin_node_id` set to `NULL` (which acts as a legacy local origin).
- A new local node identity will automatically be generated the first time the new `SyncManager` or `IdentityManager` is initialized.

## Rollback Procedure
If the migration fails or you need to downgrade, simply restore your backup:
```bash
mv memory_aegis.db.backup memory_aegis.db
```
The new Aegis runtime requires the updated schema to function, so you cannot run the new Aegis runtime on the old un-migrated schema.