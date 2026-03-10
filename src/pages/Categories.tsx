import { useMemo } from 'react';
import posts from '../data/posts.json';
import type { DailyPost, Category } from '../types';
import { categoryLabels, categoryColors } from '../types';

export function Categories() {
  const data = posts.posts as DailyPost[];
  
  const categories = useMemo(() => {
    const cats: Record<Category, number> = {
      'ai-art': 0,
      'ai-coding': 0,
      'ai-audio': 0,
      'ai-animation': 0,
      'ai-level-design': 0,
      'ai-testing': 0,
      'industry-news': 0,
    };
    
    data.forEach((post) => {
      post.articles.forEach((article) => {
        cats[article.category]++;
      });
    });
    
    return cats;
  }, [data]);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">
        <span className="gradient-text">Categories</span>
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(Object.keys(categories) as Category[]).map((cat) => (
          <a
            key={cat}
            href={`#/?category=${cat}`}
            className="flex items-center justify-between p-6 bg-slate-800/50 border border-slate-700 rounded-xl hover:border-indigo-500/50 hover:bg-slate-800 transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-lg ${categoryColors[cat]} flex items-center justify-center`}>
                <span className="text-white font-bold text-lg">
                  {categoryLabels[cat].charAt(0)}
                </span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-100 group-hover:text-indigo-400 transition-colors">
                  {categoryLabels[cat]}
                </h3>
                <p className="text-sm text-slate-400">
                  {categories[cat]} articles
                </p>
              </div>
            </div>
            <svg className="w-5 h-5 text-slate-500 group-hover:text-indigo-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </a>
        ))}
      </div>
    </div>
  );
}
