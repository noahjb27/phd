// pages/articles/[slug].tsx
import { GetStaticProps, GetStaticPaths } from 'next';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { getMarkdownData, getAllMarkdownSlugs } from '../../util/markdownParser';
import Layout from '../../components/common/Layout';

interface ArticlePostProps {
  title: string;
  date: string;
  author: string;
  content: string;
  tags?: string[];
  readingTime?: string;
}

const ArticlePost: React.FC<ArticlePostProps> = ({ 
  title, 
  date, 
  author, 
  content,
  tags,
  readingTime 
}) => (
  <Layout>
    <article className="max-w-3xl mx-auto px-4 py-8">
      {/* Back button */}
      <Link 
        href="/articles"
        className="inline-flex items-center text-sm text-gray-300 hover:text-white mb-8 transition-colors"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to all articles
      </Link>

      {/* Content container with semi-transparent background */}
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 shadow-2xl border border-white/20">
        {/* Article header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">{title}</h1>
          <div className="flex flex-wrap items-center text-sm text-gray-300 gap-4">
            <div className="flex items-center">
              <span>By {author}</span>
            </div>
            <time dateTime={date} className="text-gray-300">
              {new Date(date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </time>
            {readingTime && (
              <span className="text-gray-300">· {readingTime} read</span>
            )}
          </div>
          {tags && tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {tags.map(tag => (
                <span 
                  key={tag}
                  className="px-3 py-1 bg-purple-500/20 text-purple-200 rounded-full text-sm border border-purple-400/30"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </header>

        {/* Article content with custom prose styling for dark background */}
        <div 
          className="prose prose-lg max-w-none prose-invert prose-headings:text-white prose-p:text-gray-200 prose-a:text-blue-300 prose-a:hover:text-blue-200 prose-strong:text-white prose-em:text-gray-200 prose-code:text-pink-300 prose-code:bg-gray-800/50 prose-pre:bg-gray-800/50 prose-blockquote:border-purple-400/50 prose-blockquote:text-gray-300 prose-li:text-gray-200 prose-ul:text-gray-200 prose-ol:text-gray-200"
          dangerouslySetInnerHTML={{ __html: content }} 
        />

        {/* Article footer */}
        <footer className="mt-12 pt-8 border-t border-gray-600/50">
          <div className="flex items-center justify-between">
            <Link 
              href="/articles"
              className="text-purple-300 hover:text-purple-200 font-medium transition-colors"
            >
              ← Back to all articles
            </Link>
          </div>
        </footer>
      </div>
    </article>
  </Layout>
);

export const getStaticPaths: GetStaticPaths = async () => {
  const paths = getAllMarkdownSlugs('src/data/articles');
  return {
    paths,
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const postData = await getMarkdownData('src/data/articles', params!.slug as string);
  return {
    props: {
      ...postData,
    },
  };
};

export default ArticlePost;
