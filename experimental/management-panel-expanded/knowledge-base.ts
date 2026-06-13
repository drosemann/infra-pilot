import { promises as fs } from 'fs';
import path from 'path';

const KB_DIR = path.resolve(process.cwd(), 'data', 'knowledge-base');
const SAFE_ARTICLE_ID_RE = /^[A-Za-z0-9_-]+$/;

export interface KBArticle {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  author: string;
  authorName?: string;
  created_at: string;
  updated_at: string;
  published: boolean;
  resourceLinks?: string[];
}

export interface KBCategory {
  id: string;
  name: string;
  parentId?: string;
  description?: string;
  articleCount?: number;
}

async function ensureDir() {
  await fs.mkdir(KB_DIR, { recursive: true });
}

function sanitizeArticleId(id: string): string {
  if (!SAFE_ARTICLE_ID_RE.test(id)) {
    throw new Error('Invalid article id');
  }
  return id;
}

function articlePath(id: string): string {
  const safeId = sanitizeArticleId(id);
  const resolvedPath = path.resolve(KB_DIR, `${safeId}.md`);
  const kbRootWithSep = KB_DIR.endsWith(path.sep) ? KB_DIR : `${KB_DIR}${path.sep}`;
  if (!resolvedPath.startsWith(kbRootWithSep)) {
    throw new Error('Invalid article path');
  }
  return resolvedPath;
}

function metaPath(): string {
  return path.join(KB_DIR, '_meta.json');
}

async function getMeta(): Promise<Omit<KBArticle, 'content'>[]> {
  try {
    const raw = await fs.readFile(metaPath(), 'utf-8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function setMeta(articles: Omit<KBArticle, 'content'>[]): Promise<void> {
  await ensureDir();
  await fs.writeFile(metaPath(), JSON.stringify(articles, null, 2), 'utf-8');
}

async function getCategoriesMeta(): Promise<KBCategory[]> {
  const catPath = path.join(KB_DIR, '_categories.json');
  try {
    const raw = await fs.readFile(catPath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function setCategoriesMeta(categories: KBCategory[]): Promise<void> {
  await ensureDir();
  await fs.writeFile(path.join(KB_DIR, '_categories.json'), JSON.stringify(categories, null, 2), 'utf-8');
}

export async function listArticles(): Promise<KBArticle[]> {
  const meta = await getMeta();
  const articles: KBArticle[] = [];
  for (const m of meta) {
    try {
      const content = await fs.readFile(articlePath(m.id), 'utf-8');
      articles.push({ ...m, content });
    } catch {
      articles.push({ ...m, content: '' });
    }
  }
  return articles.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

export async function getArticle(id: string): Promise<KBArticle | null> {
  const meta = await getMeta();
  const m = meta.find(x => x.id === id);
  if (!m) return null;
  try {
    const content = await fs.readFile(articlePath(id), 'utf-8');
    return { ...m, content };
  } catch {
    return { ...m, content: '' };
  }
}

export async function createArticle(data: Partial<KBArticle>): Promise<KBArticle> {
  const meta = await getMeta();
  const id = data.id || crypto.randomUUID();
  const now = new Date().toISOString();
  const article: KBArticle = {
    id,
    title: data.title || 'Untitled',
    content: data.content || '',
    category: data.category || 'uncategorized',
    tags: data.tags || [],
    author: data.author || 'system',
    authorName: data.authorName,
    created_at: now,
    updated_at: now,
    published: data.published ?? true,
    resourceLinks: data.resourceLinks,
  };
  const metaEntry: Omit<KBArticle, 'content'> = {
    id: article.id,
    title: article.title,
    category: article.category,
    tags: article.tags,
    author: article.author,
    authorName: article.authorName,
    created_at: article.created_at,
    updated_at: article.updated_at,
    published: article.published,
    resourceLinks: article.resourceLinks,
  };
  await ensureDir();
  await fs.writeFile(articlePath(id), article.content, 'utf-8');
  meta.push(metaEntry);
  await setMeta(meta);
  return article;
}

export async function updateArticle(id: string, data: Partial<KBArticle>): Promise<KBArticle | null> {
  const existing = await getArticle(id);
  if (!existing) return null;
  const now = new Date().toISOString();
  const updated: KBArticle = {
    ...existing,
    ...data,
    id,
    updated_at: now,
  };
  const metaEntry: Omit<KBArticle, 'content'> = {
    id: updated.id,
    title: updated.title,
    category: updated.category,
    tags: updated.tags,
    author: updated.author,
    authorName: updated.authorName,
    created_at: updated.created_at,
    updated_at: updated.updated_at,
    published: updated.published,
    resourceLinks: updated.resourceLinks,
  };
  await fs.writeFile(articlePath(id), updated.content, 'utf-8');
  const meta = await getMeta();
  const idx = meta.findIndex(x => x.id === id);
  if (idx >= 0) meta[idx] = metaEntry;
  else meta.push(metaEntry);
  await setMeta(meta);
  return updated;
}

export async function deleteArticle(id: string): Promise<boolean> {
  const meta = await getMeta();
  const idx = meta.findIndex(x => x.id === id);
  if (idx < 0) return false;
  meta.splice(idx, 1);
  await setMeta(meta);
  try {
    await fs.unlink(articlePath(id));
  } catch {}
  return true;
}

export async function searchArticles(query: string): Promise<KBArticle[]> {
  const all = await listArticles();
  const q = query.toLowerCase();
  return all.filter(a =>
    a.title.toLowerCase().includes(q) ||
    a.content.toLowerCase().includes(q) ||
    a.tags.some(t => t.toLowerCase().includes(q)) ||
    a.category.toLowerCase().includes(q)
  );
}

export async function listCategories(): Promise<KBCategory[]> {
  const cats = await getCategoriesMeta();
  const articles = await getMeta();
  return cats.map(c => ({
    ...c,
    articleCount: articles.filter(a => a.category === c.name).length,
  }));
}

export async function createCategory(data: Partial<KBCategory>): Promise<KBCategory> {
  const cats = await getCategoriesMeta();
  const cat: KBCategory = {
    id: data.id || crypto.randomUUID(),
    name: data.name || 'Unnamed',
    parentId: data.parentId,
    description: data.description,
    articleCount: 0,
  };
  cats.push(cat);
  await setCategoriesMeta(cats);
  return cat;
}

export async function deleteCategory(id: string): Promise<boolean> {
  const cats = await getCategoriesMeta();
  const idx = cats.findIndex(x => x.id === id);
  if (idx < 0) return false;
  cats.splice(idx, 1);
  await setCategoriesMeta(cats);
  return true;
}
