-- Migration 004: Enable foreign key enforcement
-- IMPORTANT: This must be run at the start of every database connection.
-- SQLite requires PRAGMA foreign_keys = ON per-connection (not persistent).
-- This file serves as documentation; the application must execute this on connect.

-- Enable foreign key enforcement (must be set per-connection)
PRAGMA foreign_keys = ON;
