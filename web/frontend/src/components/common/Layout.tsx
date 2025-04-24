import Header from './Header';
import Footer from './Footer';
import PageBackground from './PageBackground';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => (
  <div className="relative min-h-screen bg-gradient-to-b from-gray-50 to-white overflow-hidden">
    <PageBackground />
    <Header />
    <main className="flex-grow container mx-auto px-4">{children}</main>
    <Footer />
  </div>
);

export default Layout;
