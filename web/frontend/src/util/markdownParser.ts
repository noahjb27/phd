import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { remark } from 'remark';
import html from 'remark-html';

export async function getMarkdownData(directory: string, slug: string) {
  const fullPath = path.join(process.cwd(), directory, `${slug}.md`);
  const fileContents = fs.readFileSync(fullPath, 'utf-8');

  const { data, content } = matter(fileContents);
  const processedContent = await remark().use(html).process(content);
  const contentHtml = processedContent.toString();

  return {
    slug,
    ...data,
    content: contentHtml,
  };
}

export function getAllMarkdownSlugs(directory: string) {
  const files = fs.readdirSync(path.join(process.cwd(), directory));
  return files.map((file) => {
    return {
      params: {
        slug: file.replace(/\.md$/, ''),
      },
    };
  });
}
