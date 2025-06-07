import React from 'react';
import Link from 'next/link';
import { Mail, Map } from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  const sections = [
    {
      title: 'Project',
      links: [
        { label: 'About', href: '/about' },
        { label: 'Blog', href: '/blog' },
        { label: 'Articles', href: '/articles' },
        { label: 'Visualizations', href: '/visualizations' },
      ]
    },
    {
      title: 'Current Work',
      links: [
        { label: 'Graph-RAG Project', href: '/current-work/graph-rag' },
        { label: 'Conferences', href: '/current-work/conferences' },
        { label: 'Presentations', href: '/current-work/presentations' },
      ]
    },
    {
      title: 'Resources',
      links: [
        { label: 'Data Sources', href: '/sources' },
        { label: 'Methodology', href: '/methodology' },
        { label: 'API Docs', href: '/api-docs' },
        { label: 'Citations', href: '/citations' },
      ]
    },
    {
      title: 'Legal',
      links: [
        { label: 'Impressum', href: '/impressum' },
        { label: 'Privacy Policy', href: '/privacy' },
        { label: 'Terms of Use', href: '/terms' },
      ]
    },
  ];

  return (
    <footer className="relative z-10 bg-gray-950/50 backdrop-blur-sm text-gray-300 border-t border-gray-700/50">
      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
          {/* Project Info */}
          <div className="md:col-span-1 space-y-4">
            <h2 className="text-xl font-bold text-white">Berlin Transport History</h2>
            <p className="text-sm text-gray-400 leading-relaxed">
              A digital history project exploring Berlin's public transportation system from 1945-1989.
            </p>
            <div className="flex space-x-4">
              <a 
                href="mailto:noah.baumann@yahoo.de"
                className="text-gray-400 hover:text-blue-400 transition-colors"
                aria-label="Email"
              >
                <Mail className="h-5 w-5" />
              </a>
              <Link
                href="/visualizations"
                className="text-gray-400 hover:text-purple-400 transition-colors"
                aria-label="Interactive Map"
              >
                <Map className="h-5 w-5" />
              </Link>
            </div>
          </div>

          {/* Navigation Sections */}
          {sections.map((section) => (
            <div key={section.title} className="md:col-span-1">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                {section.title}
              </h3>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-400 hover:text-white transition-colors hover:bg-gradient-to-r hover:from-blue-600/10 hover:to-purple-600/10 px-2 py-1 rounded -mx-2"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Academic Attribution */}
        <div className="mt-12 pt-8 border-t border-gray-800">
          <div className="text-sm text-gray-400">
            <p>
              This project is part of research conducted at{' '}
              <a 
                href="https://www.hu-berlin.de/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 transition-colors"
              >
                Humboldt University of Berlin
              </a>
            </p>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-400">
              &copy; {currentYear} Berlin Transport Project. All rights reserved.
            </p>
            <div className="mt-4 md:mt-0 flex space-x-4 text-sm text-gray-400">
              <Link href="/impressum" className="hover:text-white transition-colors">
                Impressum
              </Link>
              <span>·</span>
              <Link href="/privacy" className="hover:text-white transition-colors">
                Privacy
              </Link>
              <span>·</span>
              <Link href="/terms" className="hover:text-white transition-colors">
                Terms
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;