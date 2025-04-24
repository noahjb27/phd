// components/common/Navigation.tsx
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Menu, X } from 'lucide-react';
import { cn } from '@/util/cn';

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/visualizations', label: 'Visualizations' },
  { href: '/blog', label: 'Blog' },
  { href: '/articles', label: 'Articles' },
  { href: '/about', label: 'About' },
] as const;

const Navigation: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  // Close mobile menu on route change
  useEffect(() => {
    const handleRouteChange = () => setIsOpen(false);
    router.events.on('routeChangeStart', handleRouteChange);
    return () => router.events.off('routeChangeStart', handleRouteChange);
  }, [router]);

  // Close menu when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClick = (e: MouseEvent) => {
      if (!(e.target as Element).closest('nav')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [isOpen]);

  return (
    <nav className="relative" aria-label="Main navigation">
      {/* Mobile menu button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden p-2 rounded-md hover:bg-gray-100 transition-colors"
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
                  'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  'hover:bg-gray-100',
                  isActive 
                    ? 'text-primary bg-primary/5' 
                    : 'text-gray-700 hover:text-gray-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                {label}
              </Link>
            </li>
          )}
        )}
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
        <ul className="bg-white shadow-lg rounded-lg overflow-hidden py-1 mt-2">
          {navItems.map(({ href, label }) => {
            const isActive = router.asPath === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    'block px-4 py-2 text-sm transition-colors',
                    'hover:bg-gray-50',
                    isActive 
                      ? 'text-primary bg-primary/5 font-medium' 
                      : 'text-gray-700 hover:text-gray-900'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {label}
                </Link>
              </li>
            )}
          )}
        </ul>
      </div>
    </nav>
  );
};

export default Navigation;