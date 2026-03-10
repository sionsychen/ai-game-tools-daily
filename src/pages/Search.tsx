import { useState, useMemo } from 'react';
import { Search as SearchIcon } from 'lucide-react';
import posts from '../data/posts.json';
import type { DailyPost, Article } from '../types';
import { categoryLabels } from '../types';

export function Search() {
  const [query, setQuery] = useState('');
  const data = posts.posts as DailyPost[];

  const allArticles = useMemo(() => {
    const articles: (Article & { postDate: string })[] = [];
    data.forEach((post) => {
      post.articles.forEach((article) => {
        articles.push({ ...article, postDate: post.date });
      });
    });
    return articles;
  }, [data]);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    
    const lowerQuery = query.toLowerCase();
    return allArticles.filter((article) =>
      article.title.toLowerCase().includes(lowerQuery) ||
      article.summary.toLowerCase().includes(lowerQuery) ||
      article.tags.some((tag) => tag.toLowerCase().includes(lowerQuery)) ||
      categoryLabels[article.category].toLowerCase().includes(lowerQuery)
    );
  }, [query, allArticles]);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">
        <span className="gradient-text">Search</span>
      </h1>

      {/* Search Input */}
      <div className="relative mb-8">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search articles, tags, or categories..."
          className="w-full pl-12 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none transition-colors"
        />
      </div>

      {/* Results */}
      {query && (
        <div className="space-y-4">
          <p className="text-slate-400 mb-4">
            Found {results.length} result{results.length !== 1 ? 's' : ''}
          </p>
          
          {results.map((article) => (
            <a
              key={article.id}
              href={article.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-6 bg-slate-800/50 border border-slate-700 rounded-xl hover:border-indigo-500/50 hover:bg-slate-800 transition-all"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-medium text-indigo-400">
                  {categoryLabels[article.category]}
                </span>
                <span className="text-slate-500">·</span>
                <span className="text-xs text-slate-500">{article.postDate}</span>
              </div>
              <h3 className="text-lg font-semibold text-slate-100 mb-2">{article.title}</h3>
              <p className="text-slate-400 text-sm">{article.summary}</p>
            </a>
          ))}
          
          {results.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              No results found for "{query}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}
