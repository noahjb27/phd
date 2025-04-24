// pages/articles/index.tsx
import { useState } from 'react';
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import Link from 'next/link';
import Layout from '../../components/common/Layout';
import { Search } from 'lucide-react';

interface ArticlePost {
  slug: string;
  title: string;
  date: string;
  excerpt?: string;
  tags?: string[];
  readingTime?: string;
}

interface ArticleListProps {
  posts: ArticlePost[];
}

const ArticleList: React.FC<ArticleListProps> = ({ posts }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  // Get unique tags from all posts
  const allTags = Array.from(
    new Set(posts.flatMap(post => post.tags || []))
  ).sort();

  // Filter posts based on search term and selected tag
  const filteredPosts = posts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         post.excerpt?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTag = !selectedTag || post.tags?.includes(selectedTag);
    return matchesSearch && matchesTag;
  });

  return (
    <Layout>
      <section className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Articles</h1>
          <p className="text-lg text-gray-600">Articles on Berlin's transportation history and digital tools and methods</p>
        </div>

        {/* Search and Filter */}
        <div className="mb-8 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search articles..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {allTags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedTag(null)}
                className={`px-3 py-1 rounded-full text-sm ${
                  !selectedTag 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(tag)}
                  className={`px-3 py-1 rounded-full text-sm ${
                    selectedTag === tag
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Blog Posts Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          {filteredPosts.map(({ slug, title, date, excerpt, readingTime }) => (
            <Link 
              key={slug}
              href={`/articles/${slug}`}
              className="group block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <div className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                  {title}
                </h2>
                <div className="mt-2 flex items-center text-sm text-gray-500 space-x-4">
                  <time dateTime={date}>
                    {new Date(date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </time>
                  {readingTime && (
                    <span>· {readingTime} read</span>
                  )}
                </div>
                {excerpt && (
                  <p className="mt-3 text-gray-600 line-clamp-2">{excerpt}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      </section>
    </Layout>
  );
};

export async function getStaticProps() {
  const directory = 'src/data/articles';
  const files = fs.readdirSync(path.join(process.cwd(), directory));

  const posts = files
    .map((file) => {
      const fullPath = path.join(process.cwd(), directory, file);
      const fileContents = fs.readFileSync(fullPath, 'utf-8');
      const { data, content } = matter(fileContents);

      // Calculate reading time
      const wordsPerMinute = 200;
      const wordCount = content.split(/\s+/).length;
      const readingTime = `${Math.ceil(wordCount / wordsPerMinute)} min`;

      return {
        slug: file.replace(/\.md$/, ''),
        readingTime,
        excerpt: content.slice(0, 150) + '...',
        date: data.date,
        ...data,
      };
    })
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return {
    props: {
      posts,
    },
  };
}

export default ArticleList;
