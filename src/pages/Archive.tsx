import posts from '../data/posts.json';
import type { DailyPost } from '../types';

export function Archive() {
  const data = posts.posts as DailyPost[];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">
        <span className="gradient-text">Archive</span>
      </h1>

      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        {data.map((post, index) => (
          <a
            key={post.date}
            href={`#/${post.date}`}
            className="flex items-center justify-between px-6 py-4 hover:bg-slate-800 transition-colors border-b border-slate-700 last:border-0"
          >
            <div className="flex items-center gap-4">
              <span className="font-mono text-slate-500 w-24">
                {new Date(post.date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: '2-digit',
                })}
              </span>
              <span className="text-slate-300">
                {post.articles.length} articles
              </span>
            </div>
            <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </a>
        ))}
      </div>
    </div>
  );
}
