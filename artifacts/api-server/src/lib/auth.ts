import {
  createHmac,
  pbkdf2Sync,
  randomBytes,
  timingSafeEqual,
} from "node:crypto";
import type { Request, Response, NextFunction } from "express";
import { eq } from "drizzle-orm";
import { db, usersTable, type User } from "@workspace/db";

declare global {
  namespace Express {
    interface Request {
      currentUser?: User;
    }
  }
}

const secret =
  process.env.SESSION_SECRET ??
  (process.env.NODE_ENV === "development" ? "development-only-secret" : "");

if (!secret) {
  throw new Error("SESSION_SECRET is required outside development");
}

function b64url(value: string | Buffer): string {
  return Buffer.from(value).toString("base64url");
}

export function hashPassword(password: string): string {
  const salt = randomBytes(16);
  const digest = pbkdf2Sync(password, salt, 180_000, 32, "sha256");
  return `${salt.toString("base64url")}.${digest.toString("base64url")}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const [saltText, digestText] = stored.split(".");
  if (!saltText || !digestText) return false;
  const salt = Buffer.from(saltText, "base64url");
  const expected = Buffer.from(digestText, "base64url");
  const actual = pbkdf2Sync(password, salt, 180_000, expected.length, "sha256");
  return timingSafeEqual(actual, expected);
}

export function createToken(user: Pick<User, "id" | "role">): string {
  const payload = b64url(
    JSON.stringify({
      sub: user.id,
      role: user.role,
      exp: Math.floor(Date.now() / 1000) + 86_400,
    }),
  );
  const signature = createHmac("sha256", secret).update(payload).digest("hex");
  return `${payload}.${signature}`;
}

function decodeToken(token: string): { sub: string; exp: number } | null {
  const [payload, signature] = token.split(".");
  if (!payload || !signature) return null;
  const expected = createHmac("sha256", secret).update(payload).digest("hex");
  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  try {
    const parsed = JSON.parse(Buffer.from(payload, "base64url").toString());
    if (!parsed.sub || typeof parsed.exp !== "number" || parsed.exp < Date.now() / 1000)
      return null;
    return parsed;
  } catch {
    return null;
  }
}

export async function requireUser(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  const header = req.header("authorization") ?? "";
  const decoded = header.startsWith("Bearer ")
    ? decodeToken(header.slice(7))
    : null;
  if (!decoded) {
    res.status(401).json({ error: "Authentication required" });
    return;
  }
  const [user] = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.id, decoded.sub));
  if (!user?.isActive) {
    res.status(401).json({ error: "Invalid account" });
    return;
  }
  req.currentUser = user;
  next();
}

export async function requireAdmin(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  await requireUser(req, res, () => {
    if (req.currentUser?.role !== "admin") {
      res.status(403).json({ error: "Admin access required" });
      return;
    }
    next();
  });
}