import { useRouter } from 'next/router';
import Header from './Header';
import Footer from './Footer';
import TransportNetworkBackground from './PageBackground';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const router = useRouter();
  const isHomePage = router.pathname === '/';

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white overflow-hidden">
      <TransportNetworkBackground />
      
      {/* Only show header if not on homepage */}
      {!isHomePage && <Header />}
      
      <main className="relative z-10 flex-grow container mx-auto px-4">
        {children}
      </main>
      
      <Footer />
    </div>
  );
};

export default Layout;