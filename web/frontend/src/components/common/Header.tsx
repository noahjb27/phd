import Link from 'next/link';
import Image from 'next/image';
import Navigation from './Navigation';
import AuthButtons from './AuthButtons';

const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 bg-gray-900/80 backdrop-blur-sm border-b border-gray-700/50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link 
            href="/" 
            className="flex items-center space-x-2 text-xl font-bold text-white hover:opacity-80 transition-opacity"
          >
            <span className="sr-only">Home</span>
            <Image
              src="/assets/BPT_Logos/vector/default-monochrome.svg"
              alt="Berlin Transport Project Logo"
              width={40}
              height={40}
              className="h-8 w-auto filter invert"
            />
          </Link>

          <div className="flex items-center space-x-4">
            <Navigation />
            <div className="h-6 w-px bg-gray-600" aria-hidden="true" />
            <AuthButtons />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;