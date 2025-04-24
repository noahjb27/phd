// components/common/Header.tsx
import Link from 'next/link';
import Image from 'next/image';
import Navigation from './Navigation';
import AuthButtons from './AuthButtons';

const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link 
            href="/" 
            className="flex items-center space-x-2 text-xl font-bold text-gray-900 hover:opacity-90 transition-opacity"
          >
            <span className="sr-only">Home</span>
            <Image
              src="/assets/BPT_Logos/vector/default-monochrome.svg" // Update path based on where you store the logo
              alt="Berlin Transport Project Logo"
              width={40}
              height={40}
              className="h-8 w-auto"
            />
          </Link>

          <div className="flex items-center space-x-4">
            <Navigation />
            <div className="h-6 w-px bg-gray-200" aria-hidden="true" />
            <AuthButtons />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;