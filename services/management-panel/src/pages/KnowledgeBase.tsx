import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../lib/api';
import type { KBArticle, KBCategory } from '../lib/types';
import { CategoryTree } from '../components/KnowledgeBase/CategoryTree';
import { ArticleList } from '../components/KnowledgeBase/ArticleList';
import { ArticleEditor } from '../components/KnowledgeBase/ArticleEditor';
import { ArticleViewer } from '../components/KnowledgeBase/ArticleViewer';

export function KnowledgeBase() {
  const [articles, setArticles] = useState<KBArticle[]>([]);
  const [categories, setCategories] = useState<KBCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const loadArticles = useCallback(async () => {
    try {
      setLoading(true);
      const [arts, cats] = await Promise.all([
        apiClient.listArticles(),
        apiClient.getCategories(),
      ]);
      setArticles(arts);
      setCategories(cats);
    } catch {
      toast.error('Failed to load knowledge base');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadArticles(); }, [loadArticles]);

  const handleSearch = useCallback(async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) {
      loadArticles();
      return;
    }
    try {
      const results = await apiClient.searchArticles(q);
      setArticles(results);
    } catch {
      toast.error('Search failed');
    }
  }, [loadArticles]);

  const filteredArticles = selectedCategory
    ? articles.filter(a => a.category === categories.find(c => c.id === selectedCategory)?.name)
    : articles;

  const selectedArticle = articles.find(a => a.id === selectedArticleId) || null;

  const handleSave = async (data: Partial<KBArticle>) => {
    try {
      if (selectedArticle) {
        await apiClient.updateArticle(selectedArticle.id, data);
        toast.success('Article updated');
      } else {
        await apiClient.createArticle(data);
        toast.success('Article created');
      }
      setEditing(false);
      loadArticles();
    } catch {
      toast.error('Failed to save article');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.deleteArticle(id);
      toast.success('Article deleted');
      if (selectedArticleId === id) {
        setSelectedArticleId(null);
        setEditing(false);
      }
      loadArticles();
    } catch {
      toast.error('Failed to delete article');
    }
  };

  const handleCreate = () => {
    setSelectedArticleId(null);
    setEditing(true);
  };

  const handleAddCategory = async () => {
    const name = prompt('Category name:');
    if (!name) return;
    try {
      await apiClient.createCategory({ name });
      toast.success('Category created');
      loadArticles();
    } catch {
      toast.error('Failed to create category');
    }
  };

  const handleDeleteCategory = async (id: string) => {
    if (!confirm('Delete this category?')) return;
    try {
      await apiClient.deleteCategory(id);
      toast.success('Category deleted');
      if (selectedCategory === id) setSelectedCategory(null);
      loadArticles();
    } catch {
      toast.error('Failed to delete category');
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-2 py-8">
      <div>
        <h1 className="text-4xl font-semibold tracking-tight text-white">Knowledge Base</h1>
        <p className="mt-2 text-white/55">Internal documentation and guides.</p>
      </div>

      <div className="flex gap-6 h-[calc(100vh-280px)] min-h-[500px]">
        <div className="w-56 flex-shrink-0 card overflow-y-auto p-4">
          <CategoryTree
            categories={categories}
            selected={selectedCategory}
            onSelect={setSelectedCategory}
            onAddCategory={handleAddCategory}
            onDeleteCategory={handleDeleteCategory}
          />
        </div>

        <div className="w-72 flex-shrink-0 card overflow-y-auto p-4">
          {loading ? (
            <div className="py-8 text-center text-white/45">Loading…</div>
          ) : (
            <ArticleList
              articles={filteredArticles}
              selectedId={selectedArticleId}
              onSelect={(id) => { setSelectedArticleId(id); setEditing(false); }}
              onCreate={handleCreate}
              onDelete={handleDelete}
              onSearch={handleSearch}
              searchQuery={searchQuery}
            />
          )}
        </div>

        <div className="card flex-1 overflow-hidden p-6">
          {editing ? (
            <ArticleEditor
              article={selectedArticle}
              categories={categories}
              onSave={handleSave}
              onClose={() => setEditing(false)}
            />
          ) : selectedArticle ? (
            <ArticleViewer
              article={selectedArticle}
              onEdit={() => setEditing(true)}
              onBack={() => setSelectedArticleId(null)}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-white/45">
              <div className="text-center">
                <p className="text-lg mb-2">Select an article or create a new one</p>
                <button onClick={handleCreate} className="mt-2 text-sm text-white underline-offset-4 hover:underline">
                  Create your first article
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default KnowledgeBase;
