import Link from 'next/link';
import Layout from '../components/common/Layout';
import { ArrowRight } from 'lucide-react';

const HomePage: React.FC = () => {
  return (
    <Layout>
      <section className="relative">
        <div className="max-w-4xl mx-auto px-4 py-16 sm:py-24">
          <div className="text-center animate-fade-in">
            <h1 className="text-4xl md:text-6xl font-bold text-primary tracking-tight">
              Transporting Berlin:
              <span className="block mt-2 text-3xl md:text-5xl text-primary/90">
                A History of Movement and Change
              </span>
            </h1>

            <div className="mt-12 space-y-6 text-lg md:text-xl text-gray-600 animate-fade-in-delayed">
              <p className="text-left leading-relaxed">
                Berlin has been shaped by history like few other cities. From division to reunification, 
                its story is one of transformation and resilience. At the heart of it all lies mobility—the 
                public transport systems that have connected Berliners for over a century.
              </p>
              <p className="text-left leading-relaxed">
                This project explores how transportation evolved across regimes, how it shaped daily life, 
                and what lessons it holds for the future of urban mobility.
              </p>
            </div>

            <div className="mt-12 space-y-4 md:space-y-0 md:space-x-6 flex flex-col md:flex-row justify-center animate-fade-in-delayed-more">
              <Link 
                href="/blog" 
                className="group px-8 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition-all duration-200 transform hover:-translate-y-1 hover:shadow-lg flex items-center justify-center"
              >
                Explore the Blog
                <ArrowRight className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              
              <Link 
                href="/visualizations" 
                className="group px-8 py-3 bg-secondary text-white rounded-lg hover:bg-secondary-dark transition-all duration-200 transform hover:-translate-y-1 hover:shadow-lg flex items-center justify-center"
              >
                Dive into Visualizations
                <ArrowRight className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              
              <Link 
                href="/about" 
                className="group px-8 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-all duration-200 transform hover:-translate-y-1 hover:shadow-lg flex items-center justify-center"
              >
                About the Project
                <ArrowRight className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
};

export default HomePage;