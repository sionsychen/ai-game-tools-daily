import { ArticleCard } from '../components/ArticleCard';
import { ChevronRight } from 'lucide-react';
import type { DailyPost } from '../types';
import posts from '../data/posts.json';

export function Home() {
  const data = posts as DailyPost[];
  const latestPost = data[0];
  const archivePosts = data.slice(1, 6);

  if (!latestPost) {
    return (
      <div className="text-center py-20 text-slate-400">
        No posts yet. Check back soon!
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <section className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="gradient-text">AI Game Tools Daily</span>
        </h1>
        <p className="text-lg text-slate-400 mb-6">
          Curated AI tools and news for game development
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-full text-slate-300">
          <span>Latest Update:</span>
          <time className="font-mono text-indigo-400">
            {new Date(latestPost.date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </time>
        </div>
      </section>

      {/* Today's Headlines */}
      <section className="mb-16">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-1 h-8 bg-indigo-500 rounded-full"></div>
          <h2 className="text-2xl font-bold text-slate-100">Today's Headlines</h2>
        </div>

        <div className="space-y-6">
          {latestPost.articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      </section>

      {/* Archive Section */}
      {archivePosts.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="w-1 h-8 bg-purple-500 rounded-full"></div>
              <h2 className="text-2xl font-bold text-slate-100">Recent Archive</h2>
            </div>
            <a
              href="#/archive"
              className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
            >
              View More
              <ChevronRight className="w-4 h-4" />
            </a>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
            {archivePosts.map((post, index) => (
              <a
                key={post.date}
                href={`#/${post.date}`}
                className="flex items-center justify-between px-6 py-4 hover:bg-slate-800 transition-colors border-b border-slate-700 last:border-0"
              >
                <span className="font-mono text-slate-400">
                  {new Date(post.date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
                <span className="text-slate-300">
                  {post.articles.length} articles
                </span>
              </a>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
