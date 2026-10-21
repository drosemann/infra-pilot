// Minimal type surface for the `pg` package (it ships no type declarations
// and exports a CommonJS instance, so only the default import is typed).
// Only the members the panel actually uses are declared; anything richer can
// be narrowed at the call site.
declare module 'pg' {
  export class Pool {
    constructor(config?: unknown);
    query(
      text: string,
      values?: unknown[]
    ): Promise<{ rows: any[]; rowCount: number | null }>;
    connect(): Promise<{
      query: Pool['query'];
      release: () => void;
    }>;
    end(): Promise<void>;
    on(event: string, listener: (...args: any[]) => void): Pool;
  }
  const pg: { Pool: typeof Pool };
  export default pg;
}
