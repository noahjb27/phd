import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Menu, X, ChevronDown } from 'lucide-react';
import { cn } from '@/util/cn';

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/visualizations', label: 'Visualizations' },
  { href: '/blog', label: 'Blog' },
  { href: '/articles', label: 'Articles' },
  { href: '/about', label: 'About' },
] as const;

const currentWorkItems = [
  { href: '/current-work/graph-rag', label: 'Graph-RAG Project' },
  { href: '/current-work/conferences', label: 'Conferences' },
  { href: '/current-work/presentations', label: 'Presentations' },
] as const;

const Navigation: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCurrentWorkOpen, setIsCurrentWorkOpen] = useState(false);
  const router = useRouter();

  // Close mobile menu on route change
  useEffect(() => {
    const handleRouteChange = () => {
      setIsOpen(false);
      setIsCurrentWorkOpen(false);
    };
    router.events.on('routeChangeStart', handleRouteChange);
    return () => router.events.off('routeChangeStart', handleRouteChange);
  }, [router]);

  // Close menus when clicking outside
  useEffect(() => {
    if (!isOpen && !isCurrentWorkOpen) return;

    const handleClick = (e: MouseEvent) => {
      if (!(e.target as Element).closest('nav')) {
        setIsOpen(false);
        setIsCurrentWorkOpen(false);
      }
    };

    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [isOpen, isCurrentWorkOpen]);

  const isCurrentWorkActive = router.asPath.startsWith('/current-work');

  return (
    <nav className="relative" aria-label="Main navigation">
      {/* Mobile menu button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden p-2 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition-colors"
        aria-expanded={isOpen}
        aria-controls="mobile-menu"
        aria-label="Toggle menu"
      >
        {isOpen ? (
          <X className="w-6 h-6" aria-hidden="true" />
        ) : (
          <Menu className="w-6 h-6" aria-hidden="true" />
        )}
      </button>

      {/* Desktop navigation */}
      <ul className="hidden md:flex items-center space-x-1">
        {navItems.map(({ href, label }) => {
          const isActive = router.asPath === href;
          return (
            <li key={href}>
              <Link
                href={href}
                className={cn(
                  'px-3 py-2 rounded-md text-sm font-medium transition-all duration-200',
                  'hover:bg-gradient-to-r hover:from-blue-600/20 hover:to-purple-600/20',
                  isActive 
                    ? 'text-blue-300 bg-gradient-to-r from-blue-600/30 to-purple-600/30' 
                    : 'text-gray-300 hover:text-white'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                {label}
              </Link>
            </li>
          )}
        )}
        
        {/* Current Work Dropdown */}
        <li className="relative">
          <button
            onMouseEnter={() => setIsCurrentWorkOpen(true)}
            onMouseLeave={() => setIsCurrentWorkOpen(false)}
            className={cn(
              'flex items-center px-3 py-2 rounded-md text-sm font-medium transition-all duration-200',
              'hover:bg-gradient-to-r hover:from-purple-600/20 hover:to-blue-600/20',
              isCurrentWorkActive
                ? 'text-purple-300 bg-gradient-to-r from-purple-600/30 to-blue-600/30'
                : 'text-gray-300 hover:text-white'
            )}
            aria-expanded={isCurrentWorkOpen}
          >
            Current Work
            <ChevronDown className={cn(
              'ml-1 h-4 w-4 transition-transform duration-200',
              isCurrentWorkOpen ? 'rotate-180' : ''
            )} />
          </button>

          {/* Dropdown menu */}
          <div
            onMouseEnter={() => setIsCurrentWorkOpen(true)}
            onMouseLeave={() => setIsCurrentWorkOpen(false)}
            className={cn(
              'absolute top-full left-0 mt-1 min-w-48',
              'transform transition-all duration-200 ease-in-out',
              isCurrentWorkOpen 
                ? 'translate-y-0 opacity-100 pointer-events-auto' 
                : '-translate-y-2 opacity-0 pointer-events-none'
            )}
          >
            <ul className="bg-gray-800/95 backdrop-blur-sm shadow-lg rounded-lg overflow-hidden py-1 border border-gray-700/50">
              {currentWorkItems.map(({ href, label }) => {
                const isActive = router.asPath === href;
                return (
                  <li key={href}>
                    <Link
                      href={href}
                      className={cn(
                        'block px-4 py-2 text-sm transition-all duration-200',
                        'hover:bg-gradient-to-r hover:from-purple-600/20 hover:to-blue-600/20',
                        isActive 
                          ? 'text-purple-300 bg-gradient-to-r from-purple-600/30 to-blue-600/30 font-medium' 
                          : 'text-gray-300 hover:text-white'
                      )}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      {label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </li>
      </ul>

      {/* Mobile menu */}
      <div
        id="mobile-menu"
        className={cn(
          'absolute top-full left-0 right-0 md:hidden',
          'transform transition-all duration-200 ease-in-out',
          isOpen ? 'translate-y-0 opacity-100' : '-translate-y-2 opacity-0 pointer-events-none'
        )}
      >
        <ul className="bg-gray-800/95 backdrop-blur-sm shadow-lg rounded-lg overflow-hidden py-1 mt-2 border border-gray-700/50">
          {navItems.map(({ href, label }) => {
            const isActive = router.asPath === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    'block px-4 py-2 text-sm transition-colors',
                    'hover:bg-gradient-to-r hover:from-blue-600/20 hover:to-purple-600/20',
                    isActive 
                      ? 'text-blue-300 bg-gradient-to-r from-blue-600/30 to-purple-600/30 font-medium' 
                      : 'text-gray-300 hover:text-white'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {label}
                </Link>
              </li>
            )}
          )}
          
          {/* Current Work mobile section */}
          <li className="border-t border-gray-700/50 mt-1 pt-1">
            <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Current Work
            </div>
            {currentWorkItems.map(({ href, label }) => {
              const isActive = router.asPath === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    'block px-6 py-2 text-sm transition-colors',
                    'hover:bg-gradient-to-r hover:from-purple-600/20 hover:to-blue-600/20',
                    isActive 
                      ? 'text-purple-300 bg-gradient-to-r from-purple-600/30 to-blue-600/30 font-medium' 
                      : 'text-gray-300 hover:text-white'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {label}
                </Link>
              );
            })}
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navigation;