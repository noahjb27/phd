// pages/blog/index.tsx
import { useState } from 'react';
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import Link from 'next/link';
import Layout from '../../components/common/Layout';
import { Search } from 'lucide-react';

interface BlogPost {
  slug: string;
  title: string;
  date: string;
  excerpt?: string;
  tags?: string[];
  readingTime?: string;
}

interface BlogListProps {
  posts: BlogPost[];
}

const BlogList: React.FC<BlogListProps> = ({ posts }) => {
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
        {/* Header */}
        <div className="text-center mb-12">
          <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20">
            <h1 className="text-4xl font-bold text-white mb-4">Blog</h1>
            <p className="text-lg text-blue-100">Personal thoughts and reflections on public transportation and digital history</p>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="mb-8 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search posts..."
              className="w-full pl-10 pr-4 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {allTags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedTag(null)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  !selectedTag 
                    ? 'bg-blue-500/30 text-blue-200 border border-blue-400/50' 
                    : 'bg-white/10 text-gray-300 hover:bg-white/20 border border-white/20'
                }`}
              >
                All
              </button>
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(tag)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    selectedTag === tag
                      ? 'bg-blue-500/30 text-blue-200 border border-blue-400/50'
                      : 'bg-white/10 text-gray-300 hover:bg-white/20 border border-white/20'
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
              href={`/blog/${slug}`}
              className="group block bg-white/10 backdrop-blur-sm rounded-lg shadow-sm hover:shadow-md hover:bg-white/15 transition-all duration-200 border border-white/20"
            >
              <div className="p-6">
                <h2 className="text-xl font-semibold text-white group-hover:text-blue-300 transition-colors">
                  {title}
                </h2>
                <div className="mt-2 flex items-center text-sm text-gray-400 space-x-4">
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
                  <p className="mt-3 text-gray-300 line-clamp-2">{excerpt}</p>
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
  const directory = 'src/data/blog';
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

export default BlogList;