import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { runMigrations } from "./migrate.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function resolveSchemaPath(): string {
  const localSchema = path.join(__dirname, "schema.sql");
  if (fs.existsSync(localSchema)) {
    return localSchema;
  }

  // When the plugin runs from dist/, TypeScript does not copy .sql assets by default.
  // Fall back to the source tree schema so packaged local installs still work.
  const sourceSchema = path.resolve(__dirname, "../../../src/db/schema.sql");
  if (fs.existsSync(sourceSchema)) {
    return sourceSchema;
  }

  return localSchema;
}

export interface AegisDatabase {
  readonly db: Database.Database;
  close(): void;
}

/**
 * Open or create the Aegis v3 SQLite database.
 *
 * - Creates parent directory if needed
 * - Enables WAL mode for concurrent reads
 * - Enables foreign keys
 * - Runs schema initialization (idempotent via IF NOT EXISTS)
 */
export function openDatabase(dbPath: string): AegisDatabase {
  const dir = path.dirname(dbPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  const db = new Database(dbPath);

  // Performance & safety pragmas
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");
  db.pragma("busy_timeout = 5000");
  db.pragma("synchronous = NORMAL");
  db.pragma("cache_size = -64000"); // 64MB cache

  // Initialize schema (all CREATE IF NOT EXISTS — safe to re-run)
  const schema = fs.readFileSync(resolveSchemaPath(), "utf-8");
  db.exec(schema);

  // Run migrations to bring schema up to latest version
  runMigrations(db);

  return {
    db,
    close() {
      if (db.open) {
        db.close();
      }
    },
  };
}

/**
 * Resolve the default database path for an agent.
 */
export function resolveDbPath(workspaceDir: string): string {
  return path.join(workspaceDir, "memory-aegis.db");
}
