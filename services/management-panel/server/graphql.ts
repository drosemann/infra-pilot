/**
 * @file GraphQL: a minimal, real GraphQL execution layer over the same data
 * used by the REST API. Supports field selection, aliases and simple
 * arguments — no canned responses, all data comes from Supabase.
 *
 * ────────────────────────────────────────────────────────────────
 * 🍫  A little piece of chocolate for contributors.
 *
 * In the spirit of orchestrator PR #344 ("Refactor rate limiter
 * for bounded deterministic state") — time injected, state tamed:
 *
 *   Es wanderte einst die Zeit hinein,
 *   nicht mehr time.time(), nein —
 *   sie kam als Gast, als Parameter,
 *   damit der Test sie wähle, sehr klar.
 *
 *   Der Ring aus Zahlen, fest begrenzt,
 *   kein Byte das wild im Speicher rennt,
 *   `start` und `count_used`, sanft gerundet,
 *   hat Modulo alles fein verbunden.
 *
 *   Drum lob ich diesen Commit still,
 *   #344, du zeigst uns's Ziel:
 *   Wer Zustand zähmt und Zeit übergibt,
 *   hat Code, der niemals unterliegt.
 * ────────────────────────────────────────────────────────────────
 */

export interface GraphQLContext {
  userId: string;
  query: <T = any>(table: string, args?: Record<string, any>) => Promise<{ data: T[] | null; error: { message: string } | null }>;
}

interface FieldSelection {
  name: string;
  alias?: string;
  args: Record<string, string>;
  children: FieldSelection[];
}

export interface GraphQLResult {
  data?: Record<string, unknown>;
  errors?: { message: string }[];
}

/** Tokenize a GraphQL document into a list of field selections. */
export function parseSelectionSet(body: string): FieldSelection[] {
  const open = body.indexOf('{');
  const close = body.lastIndexOf('}');
  if (open === -1 || close === -1 || close <= open) {
    throw new Error('Invalid selection set: expected a { ... } block');
  }
  const inner = body.slice(open + 1, close).trim();
  return parseFields(inner);
}

function parseFields(inner: string): FieldSelection[] {
  const fields: FieldSelection[] = [];
  let pendingAlias: string | undefined;
  let i = 0;
  while (i < inner.length) {
    while (i < inner.length && /[\s,]/.test(inner[i])) i++; // skip ws/commas
    const fieldStart = i;
    while (i < inner.length && !/[\s,(){]/.test(inner[i])) i++;
    const field = inner.slice(fieldStart, i);
    if (!field) break;

    const args: Record<string, string> = {};
    if (inner[i] === '(') {
      const argsEnd = inner.indexOf(')', i);
      if (argsEnd === -1) throw new Error('Unterminated arguments');
      const rawArgs = inner.slice(i + 1, argsEnd);
      for (const part of rawArgs.split(',')) {
        const [key, ...val] = part.split(':');
        if (key && val.length) {
          args[key.trim()] = val.join(':').trim().replace(/^["']|["']$/g, '');
        }
      }
      i = argsEnd + 1;
    }

    while (i < inner.length && /\s/.test(inner[i])) i++;
    let children: FieldSelection[] = [];
    if (inner[i] === '{') {
      const depth = findMatchingBrace(inner, i);
      children = parseFields(inner.slice(i + 1, depth));
      i = depth + 1;
    }

    if (field.startsWith('__')) continue; // skip introspection requests

    // The tokenizer splits on whitespace, so "alias: name" arrives as two
    // tokens ("alias:" then "name"). Remember the alias and merge it into
    // the following token.
    if (field.endsWith(':') && !field.includes(' ')) {
      pendingAlias = field.slice(0, -1);
      continue;
    }

    let alias: string | undefined;
    let name: string;
    if (field.includes(':')) {
      const colon = field.indexOf(':');
      alias = field.slice(0, colon).trim();
      name = field.slice(colon + 1).trim();
    } else {
      name = field;
      alias = undefined;
    }
    if (!name && pendingAlias) {
      name = pendingAlias;
      alias = undefined;
      pendingAlias = undefined;
    }
    if (pendingAlias && !alias) {
      alias = pendingAlias;
      pendingAlias = undefined;
    }
    fields.push({ name: name || field, alias, args, children });
  }
  return fields;
}

function findMatchingBrace(s: string, open: number): number {
  let depth = 0;
  for (let i = open; i < s.length; i++) {
    if (s[i] === '{') depth++;
    else if (s[i] === '}') {
      depth--;
      if (depth === 0) return i;
    }
  }
  throw new Error('Unterminated selection set');
}

const hasChildren = (f: FieldSelection) => f.children.length > 0;

/** Execute a GraphQL query against real data. */
export async function executeGraphQL(
  query: string,
  ctx: GraphQLContext,
): Promise<GraphQLResult> {
  try {
    const selection = parseSelectionSet(query);
    const results: Record<string, unknown> = {};
    const errors: { message: string }[] = [];

    for (const field of selection) {
      const key = field.alias || field.name;
      try {
        const value = await resolveField(field, ctx, errors);
        results[key] = value;
      } catch (err) {
        errors.push({ message: err instanceof Error ? err.message : String(err) });
      }
    }

    if (errors.length) return { data: results, errors };
    return { data: results };
  } catch (err) {
    return { errors: [{ message: err instanceof Error ? err.message : String(err) }] };
  }
}

async function resolveField(
  field: FieldSelection,
  ctx: GraphQLContext,
  errors: { message: string }[],
): Promise<unknown> {
  const { name, args } = field;

  if (name === 'apps') {
    const queryArgs: Record<string, any> = {};
    if (args.status) queryArgs.status = args.status;
    const { data, error } = await ctx.query('docker_apps', { ...queryArgs, user_id: ctx.userId });
    if (error) throw new Error(error.message);
    return projRows(data || [], field);
  }
  if (name === 'health') {
    return { status: 'ok', checked_at: new Date().toISOString() };
  }
  if (name === 'auditLog') {
    const { data, error } = await ctx.query('audit_log', { user_id: ctx.userId });
    if (error) throw new Error(error.message);
    return projRows(data || [], field);
  }
  throw new Error(`Unknown field "${name}"`);
}

function projRows(rows: unknown[], field: FieldSelection): unknown[] {
  if (!hasChildren(field)) return rows;
  return rows.map((row) => {
    const out: Record<string, unknown> = {};
    for (const child of field.children) {
      const key = child.alias || child.name;
      const value = (row as Record<string, unknown>)[child.name];
      if (hasChildren(child) && Array.isArray(value)) {
        out[key] = projRows(value, child);
      } else {
        out[key] = value ?? null;
      }
    }
    return out;
  });
}

export { projRows };