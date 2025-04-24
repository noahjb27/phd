// components/common/Footer.tsx
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
      title: 'Resources',
      links: [
        { label: 'About', href: '/about' },
        { label: 'Data Sources', href: '/sources' },
        { label: 'Methodology', href: '/methodology' },
        { label: 'API', href: '/api-docs' },
      ]
    },
    {
      title: 'Legal',
      links: [
        { label: 'Impressum', href: '/impressum' },
        { label: 'Privacy Policy', href: '/privacy' },
        { label: 'Terms of Use', href: '/terms' },
        { label: 'Citations', href: '/citations' },
      ]
    },
  ];

  return (
    <footer className="bg-gray-900 text-gray-300">
      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Project Info */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white">Berlin Public Transport History</h2>
            <p className="text-sm text-gray-400">
              A digital history project exploring Berlin's public transportation system from 1945-1989.
            </p>
            <div className="flex space-x-4">
              <a 
                href="mailto:contact@project.com"
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Email"
              >
                <Mail className="h-5 w-5" />
              </a>
              <Link
                href="/map"
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Interactive Map"
              >
                <Map className="h-5 w-5" />
              </Link>
            </div>
          </div>

          {/* Navigation Sections */}
          {sections.map((section) => (
            <div key={section.title}>
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                {section.title}
              </h3>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-400 hover:text-white transition-colors"
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
                className="text-blue-400 hover:text-blue-300"
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