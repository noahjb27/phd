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
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-8"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to all articles
      </Link>

      {/* Article header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">{title}</h1>
        <div className="flex flex-wrap items-center text-sm text-gray-600 gap-4">
          <div className="flex items-center">
            {/* You could add an avatar here */}
            <span>By {author}</span>
          </div>
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
        {tags && tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {tags.map(tag => (
              <span 
                key={tag}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* Article content */}
      <div 
        className="prose prose-lg max-w-none prose-blue prose-img:rounded-lg prose-headings:text-gray-900"
        dangerouslySetInnerHTML={{ __html: content }} 
      />

      {/* Article footer */}
      <footer className="mt-12 pt-8 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <Link 
            href="/articles"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to all articles
          </Link>
          {/* You could add social share buttons here */}
        </div>
      </footer>
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
