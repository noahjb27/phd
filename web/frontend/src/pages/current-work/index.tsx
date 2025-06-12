// pages/current-work/index.tsx
import Layout from '@/components/common/Layout';
import Link from 'next/link';
import { ArrowRight, Bot, Users, Presentation, Calendar, FileText, ExternalLink } from 'lucide-react';

const CurrentWorkPage = () => {
  return (
    <Layout>
      <div className="py-12">
        {/* Hero Section */}
        <div className="max-w-5xl mx-auto px-6 mb-16">
          <div className="bg-gradient-to-br from-purple-600/90 to-blue-600/90 rounded-xl p-8 shadow-2xl border border-purple-400/20">
            <h1 className="text-4xl md:text-5xl font-bold text-white text-center mb-6">
              Current Work
            </h1>
            <p className="text-xl text-purple-100 text-center max-w-3xl mx-auto leading-relaxed">
              Exploring the intersection of AI, digital humanities, and historical research
            </p>
          </div>
        </div>

        {/* Current Projects Grid */}
        <div className="max-w-5xl mx-auto px-6 mb-16">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Graph-RAG Project */}
            <Link href="/current-work/graph-rag">
              <div className="bg-gradient-to-br from-blue-600/90 to-cyan-600/90 rounded-xl p-6 shadow-2xl border border-blue-400/20 hover:shadow-3xl transition-all duration-200 transform hover:-translate-y-2 group cursor-pointer">
                <div className="flex items-center mb-4">
                  <div className="bg-white/20 backdrop-blur-sm p-3 rounded-full mr-4">
                    <Bot className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Graph-RAG Project</h3>
                </div>
                <p className="text-blue-100 mb-4">
                  Experimenting with AI-powered knowledge graphs for historical research. 
                  Combining Neo4j with large language models to make historical data more accessible.
                </p>
                <div className="flex items-center text-cyan-300 group-hover:text-cyan-200 transition-colors">
                  <span className="text-sm font-medium">Learn more</span>
                  <ArrowRight className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </Link>

            {/* Conferences */}
            <Link href="/current-work/conferences">
              <div className="bg-gradient-to-br from-green-600/90 to-blue-600/90 rounded-xl p-6 shadow-2xl border border-green-400/20 hover:shadow-3xl transition-all duration-200 transform hover:-translate-y-2 group cursor-pointer">
                <div className="flex items-center mb-4">
                  <div className="bg-white/20 backdrop-blur-sm p-3 rounded-full mr-4">
                    <Users className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Conferences</h3>
                </div>
                <p className="text-green-100 mb-4">
                  Upcoming and past conference presentations on digital history methods, 
                  transport networks, and computational approaches to historical research.
                </p>
                <div className="flex items-center text-blue-300 group-hover:text-blue-200 transition-colors">
                  <span className="text-sm font-medium">View schedule</span>
                  <ArrowRight className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </Link>

            {/* Presentations */}
            <Link href="/current-work/presentations">
              <div className="bg-gradient-to-br from-purple-600/90 to-pink-600/90 rounded-xl p-6 shadow-2xl border border-purple-400/20 hover:shadow-3xl transition-all duration-200 transform hover:-translate-y-2 group cursor-pointer">
                <div className="flex items-center mb-4">
                  <div className="bg-white/20 backdrop-blur-sm p-3 rounded-full mr-4">
                    <Presentation className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Presentations</h3>
                </div>
                <p className="text-purple-100 mb-4">
                  Slides and materials from talks on Berlin's transport history, 
                  digital humanities tools, and collaborative research methods.
                </p>
                <div className="flex items-center text-pink-300 group-hover:text-pink-200 transition-colors">
                  <span className="text-sm font-medium">View materials</span>
                  <ArrowRight className="ml-2 h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </Link>
          </div>
        </div>

        {/* Recent Updates */}
        <div className="max-w-5xl mx-auto px-6">
          <div className="bg-gradient-to-br from-gray-700/90 to-gray-600/90 rounded-xl p-8 shadow-2xl border border-gray-500/20">
            <h2 className="text-3xl font-bold text-white mb-8 text-center">Recent Updates</h2>
            
            <div className="space-y-6">
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                      Graph-RAG Implementation Progress
                    </h3>
                    <div className="flex items-center text-gray-300 text-sm">
                      <Calendar className="h-4 w-4 mr-2" />
                      <span>January 2025</span>
                    </div>
                  </div>
                  <FileText className="h-6 w-6 text-gray-400" />
                </div>
                <p className="text-gray-300 mb-4">
                  Successfully integrated Claude 3.5 Sonnet with our Neo4j transport network database. 
                  Users can now ask natural language questions about Berlin's historical transport connections.
                </p>
                <Link 
                  href="/current-work/graph-rag" 
                  className="inline-flex items-center text-blue-400 hover:text-blue-300 font-medium transition-colors"
                >
                  Read full update
                  <ExternalLink className="ml-1 h-4 w-4" />
                </Link>
              </div>

              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                      DH Conference Proposals Submitted
                    </h3>
                    <div className="flex items-center text-gray-300 text-sm">
                      <Calendar className="h-4 w-4 mr-2" />
                      <span>December 2024</span>
                    </div>
                  </div>
                  <Users className="h-6 w-6 text-gray-400" />
                </div>
                <p className="text-gray-300 mb-4">
                  Submitted proposals for DH2025 and THATCamp focusing on collaborative 
                  digital history workflows and public engagement with historical data.
                </p>
                <Link 
                  href="/current-work/conferences" 
                  className="inline-flex items-center text-green-400 hover:text-green-300 font-medium transition-colors"
                >
                  View conference details
                  <ExternalLink className="ml-1 h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default CurrentWorkPage;