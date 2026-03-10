export type Category = 
  | 'ai-art' 
  | 'ai-coding' 
  | 'ai-audio' 
  | 'ai-animation' 
  | 'ai-level-design' 
  | 'ai-testing' 
  | 'industry-news';

export interface Article {
  id: string;
  title: string;
  date: string;
  category: Category;
  tags: string[];
  sourceUrl: string;
  sourceName: string;
  summary: string;
}

export interface DailyPost {
  date: string;
  articles: Article[];
}

export const categoryLabels: Record<Category, string> = {
  'ai-art': 'AI Art Tools',
  'ai-coding': 'AI Coding',
  'ai-audio': 'AI Audio',
  'ai-animation': 'AI Animation',
  'ai-level-design': 'AI Level Design',
  'ai-testing': 'AI Testing',
  'industry-news': 'Industry News',
};

export const categoryColors: Record<Category, string> = {
  'ai-art': 'bg-pink-600',
  'ai-coding': 'bg-blue-600',
  'ai-audio': 'bg-green-600',
  'ai-animation': 'bg-orange-600',
  'ai-level-design': 'bg-purple-600',
  'ai-testing': 'bg-red-600',
  'industry-news': 'bg-slate-600',
};
