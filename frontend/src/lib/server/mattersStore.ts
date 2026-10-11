/**
 * Persistent Matters Storage Helper
 * =================================
 * Provides read/write access to matters data with graceful fallback for
 * read-only serverless filesystems (e.g., Vercel / AWS Lambda /var/task).
 */

import fs from "fs";
import path from "path";
import os from "os";
import { INITIAL_MATTERS } from "@/lib/data/matters";
import { Matter } from "@/lib/types/matter";

const PRIMARY_MATTERS_PATH = path.resolve(
  process.cwd(),
  "src",
  "lib",
  "data",
  "extracted_matters.json"
);

const SERVERLESS_MATTERS_PATH = path.resolve(
  os.tmpdir(),
  "vidhik_storage",
  "extracted_matters.json"
);

export function loadAllMatters(): Matter[] {
  let baseMatters: Matter[] = [];

  if (fs.existsSync(PRIMARY_MATTERS_PATH)) {
    try {
      const data = fs.readFileSync(PRIMARY_MATTERS_PATH, "utf-8");
      baseMatters = JSON.parse(data);
    } catch {
      baseMatters = [...INITIAL_MATTERS];
    }
  } else {
    baseMatters = [...INITIAL_MATTERS];
  }

  // If serverless tmp file exists, merge/overlay any newer matters
  if (fs.existsSync(SERVERLESS_MATTERS_PATH)) {
    try {
      const tmpData = fs.readFileSync(SERVERLESS_MATTERS_PATH, "utf-8");
      const tmpMatters: Matter[] = JSON.parse(tmpData);
      const matterMap = new Map<string, Matter>();
      // Base matters first
      for (const m of baseMatters) {
        if (m && m.id) matterMap.set(m.id, m);
      }
      // Overlay tmp matters
      for (const m of tmpMatters) {
        if (m && m.id) matterMap.set(m.id, m);
      }
      return Array.from(matterMap.values());
    } catch {
      // Ignore tmp read errors
    }
  }

  return baseMatters;
}

export function saveAllMatters(matters: Matter[]): void {
  const payload = JSON.stringify(matters, null, 2);

  // 1. Try primary location (works in local dev / persistent server)
  let wrotePrimary = false;
  try {
    const parentDir = path.dirname(PRIMARY_MATTERS_PATH);
    if (fs.existsSync(parentDir)) {
      fs.writeFileSync(PRIMARY_MATTERS_PATH, payload, "utf-8");
      wrotePrimary = true;
    }
  } catch {
    wrotePrimary = false;
  }

  // 2. Always sync to serverless tmp location if running serverless or primary write failed
  const isServerless =
    !wrotePrimary ||
    Boolean(process.env.VERCEL) ||
    Boolean(process.env.AWS_LAMBDA_FUNCTION_NAME) ||
    process.cwd().startsWith("/var/task");

  if (isServerless) {
    try {
      const tmpDir = path.dirname(SERVERLESS_MATTERS_PATH);
      if (!fs.existsSync(tmpDir)) {
        fs.mkdirSync(tmpDir, { recursive: true });
      }
      fs.writeFileSync(SERVERLESS_MATTERS_PATH, payload, "utf-8");
    } catch (err: any) {
      console.warn("Could not write matters to serverless tmp store:", err.message);
    }
  }
}
