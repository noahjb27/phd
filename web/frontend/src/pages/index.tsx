import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, Play, BookOpen, BarChart3, User, Calendar } from 'lucide-react';

const TransportAnimation = () => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const totalScrollable = documentHeight - windowHeight;
      const progress = Math.min(scrollTop / (totalScrollable * 0.8), 1); // Complete animation in first 80% of page
      setScrollProgress(progress);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0 overflow-hidden">
      {/* Subtle background tracks/lines */}
      <div className="absolute top-1/3 w-full opacity-20">
        <div className="h-px bg-blue-400 mb-16"></div>
        <div className="h-px bg-purple-400 mb-16"></div>
        <div className="h-px bg-blue-400"></div>
      </div>
      
      {/* Bus - slowest */}
      <div 
        className="absolute transition-all duration-300 ease-out"
        style={{
          left: `${(scrollProgress * 120 * 0.6)}%`, // 60% speed
          top: '30%',
          transform: 'translateY(-50%)',
        }}
      >
        <div className="flex items-center">
          <Image
            src="/images/bus-1980s.png"
            alt="1980s Berlin Bus"
            width={80}
            height={40}
            className="object-contain filter drop-shadow-lg"
          />
          <div className="ml-2 text-sm font-medium text-purple-300 whitespace-nowrap">Bus</div>
        </div>
      </div>

      {/* Tram - medium speed */}
      <div 
        className="absolute transition-all duration-300 ease-out"
        style={{
          left: `${100 - (scrollProgress * 120 * 0.8)}%`, // 80% speed
          top: '50%',
          transform: 'translateY(-50%)',
        }}
      >
        <div className="flex items-center">
          <Image
            src="/images/tram-1980s.png"
            alt="1980s Berlin Tram"
            width={80}
            height={40}
            className="object-contain filter drop-shadow-lg"
          />
          <div className="ml-2 text-sm font-medium text-red-300 whitespace-nowrap">Tram</div>
        </div>
      </div>

      {/* S-Bahn - fastest */}
      <div 
        className="absolute transition-all duration-300 ease-out"
        style={{
          left: `${(scrollProgress * 120)}%`, // 100% speed
          top: '70%',
          transform: 'translateY(-50%)',
        }}
      >
        <div className="flex items-center">
          <Image
            src="/images/train-1980s.png"
            alt="1980s Berlin S-Bahn"
            width={80}
            height={40}
            className="object-contain filter drop-shadow-lg"
          />
          <div className="ml-2 text-sm font-medium text-blue-300 whitespace-nowrap">U-Bahn</div>
        </div>
      </div>
    </div>
  );
};

const HomePage = () => {
  return (
    <div className="relative min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 overflow-hidden">
      <TransportAnimation />
      
      {/* Main content with higher z-index */}
      <div className="relative z-10">
        {/* Hero Section */}
        <section className="min-h-screen flex items-center">
          <div className="max-w-4xl mx-auto px-6 py-16">
            <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 backdrop-blur-sm rounded-xl p-8 shadow-2xl border border-blue-400/20">
              <div className="text-center mb-8">
                <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
                  Transporting Berlin
                </h1>
                <p className="text-xl md:text-2xl text-blue-100 mb-8">
                  See how a divided city moved its people — and what it means for today
                </p>
                <p className="text-lg text-blue-50 max-w-3xl mx-auto leading-relaxed">
                  Explore how Cold War politics shaped daily life through Berlin's public transport. 
                  Which neighborhoods gained access? Which lost out? And what can we learn for cities today?
                </p>
              </div>

              <div className="flex flex-col md:flex-row gap-4 justify-center">
                <Link 
                  href="/visualizations" 
                  className="group px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-all duration-200 transform hover:-translate-y-1 hover:shadow-lg flex items-center justify-center font-semibold"
                >
                  <Play className="mr-2 h-5 w-5" />
                  Explore the Maps
                  <ArrowRight className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
                
                <Link 
                  href="/about" 
                  className="group px-8 py-3 bg-blue-800/50 text-white border border-blue-400/30 rounded-lg hover:bg-blue-700/50 transition-all duration-200 transform hover:-translate-y-1 hover:shadow-md flex items-center justify-center"
                >
                  <User className="mr-2 h-5 w-5" />
                  About the Project
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* What is Digital History */}
        <section className="py-16">
          <div className="max-w-4xl mx-auto px-6">
            <div className="bg-gradient-to-br from-purple-600/90 to-blue-600/90 rounded-xl p-8 shadow-2xl border border-purple-400/20">
              <h2 className="text-3xl font-bold text-center mb-8 text-white">What is Digital History?</h2>
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <p className="text-lg text-purple-50 leading-relaxed mb-4">
                    Digital history combines traditional historical research with modern technology. 
                    Instead of just reading about the past, we can visualize it, interact with it, 
                    and discover patterns that would be impossible to see otherwise.
                  </p>
                  <p className="text-lg text-purple-50 leading-relaxed">
                    This project uses databases, interactive maps, and data visualization 
                    to bring Berlin's transport history to life.
                  </p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                  <h3 className="text-xl font-semibold mb-4 text-white">Why Berlin Transport?</h3>
                  <ul className="space-y-2 text-purple-100">
                    <li>• A city literally divided by politics</li>
                    <li>• Two competing visions of urban planning</li>
                    <li>• Real impact on daily life for millions</li>
                    <li>• Lessons for cities today</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Your Guide to DH */}
        <section className="py-16">
          <div className="max-w-4xl mx-auto px-6">
            <div className="bg-gradient-to-br from-blue-600/90 to-indigo-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20">
              <div className="text-center mb-12">
                <h2 className="text-3xl font-bold mb-4 text-white">Your Guide to Digital History</h2>
                <p className="text-xl text-blue-100">
                  Hi, I'm Noah. I'm a PhD student learning to combine history with technology, 
                  and I want to share that journey with you.
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="bg-white/20 backdrop-blur-sm p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center border border-white/30">
                    <BarChart3 className="h-8 w-8 text-blue-200" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2 text-white">The Tools</h3>
                  <p className="text-blue-100">
                    Neo4j, React, Python—learn why I chose them and how they work
                  </p>
                </div>

                <div className="text-center">
                  <div className="bg-white/20 backdrop-blur-sm p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center border border-white/30">
                    <BookOpen className="h-8 w-8 text-green-200" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2 text-white">The Process</h3>
                  <p className="text-blue-100">
                    From archival research to interactive maps—behind the scenes
                  </p>
                </div>

                <div className="text-center">
                  <div className="bg-white/20 backdrop-blur-sm p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center border border-white/30">
                    <User className="h-8 w-8 text-purple-200" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2 text-white">The Learning</h3>
                  <p className="text-blue-100">
                    Mistakes, breakthroughs, and everything I wish I'd known
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Latest Updates */}
        <section className="py-16">
          <div className="max-w-4xl mx-auto px-6">
            <div className="bg-gradient-to-br from-indigo-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-indigo-400/20">
              <h2 className="text-3xl font-bold text-center mb-8 text-white">Latest Updates</h2>
              <div className="grid md:grid-cols-2 gap-8">
                <div className="border-l-4 border-blue-300 pl-6">
                  <h3 className="text-xl font-semibold mb-2 text-white">Blog</h3>
                  <p className="text-indigo-100 mb-4">
                    Personal thoughts on transport, cities, and learning to code as a historian
                  </p>
                  <Link 
                    href="/blog" 
                    className="text-blue-300 hover:text-blue-200 font-medium inline-flex items-center transition-colors"
                  >
                    Read latest posts
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Link>
                </div>

                <div className="border-l-4 border-green-300 pl-6">
                  <h3 className="text-xl font-semibold mb-2 text-white">Articles</h3>
                  <p className="text-indigo-100 mb-4">
                    Deep dives into methods, tools, and findings from the project
                  </p>
                  <Link 
                    href="/articles" 
                    className="text-green-300 hover:text-green-200 font-medium inline-flex items-center transition-colors"
                  >
                    View all articles
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Call to Action */}
        <section className="py-16 text-center">
          <div className="max-w-4xl mx-auto px-6">
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-8 text-white shadow-2xl border border-purple-400/30">
              <h2 className="text-3xl font-bold mb-4">Ready to Explore?</h2>
              <p className="text-xl mb-8 text-purple-100">
                Dive into the interactive maps and see how Berlin's story unfolds
              </p>
              <Link 
                href="/visualizations" 
                className="inline-flex items-center px-8 py-3 bg-white text-purple-600 rounded-lg hover:bg-purple-50 transition-colors font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                <Play className="mr-2 h-5 w-5" />
                Start Exploring
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default HomePage;