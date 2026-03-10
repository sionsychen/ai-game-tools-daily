import { ExternalLink } from 'lucide-react';
import type { Article } from '../types';
import { categoryLabels, categoryColors } from '../types';

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  return (
    <article className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 hover:border-indigo-500/50 hover:bg-slate-800 transition-all duration-300 group">
      {/* Category Badge */}
      <div className="flex items-center gap-2 mb-4">
        <span className={`px-3 py-1 rounded-full text-xs font-medium text-white ${categoryColors[article.category]}`}>
          {categoryLabels[article.category]}
        </span>
        {article.tags.map((tag) => (
          <span key={tag} className="px-2 py-1 rounded-full text-xs bg-slate-700 text-slate-300">
            #{tag}
          </span>
        ))}
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold text-slate-100 mb-3 group-hover:text-indigo-400 transition-colors">
        {article.title}
      </h3>

      {/* Source & Date */}
      <div className="flex items-center gap-2 text-sm text-slate-400 mb-4">
        <span>{article.sourceName}</span>
        <span>·</span>
        <time>{new Date(article.date).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        })}</time>
      </div>

      {/* Summary */}
      <p className="text-slate-300 leading-relaxed mb-4">
        {article.summary}
      </p>

      {/* Read More Link */}
      <a
        href={article.sourceUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
      >
        Read Original
        <ExternalLink className="w-4 h-4" />
      </a>
    </article>
  );
}
