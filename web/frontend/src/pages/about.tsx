import { useState } from 'react';
import Link from 'next/link';
import Layout from '../components/common/Layout';
import { 
  Book, 
  BarChart3, 
  Mail, 
  Clock, 
  Map, 
  GraduationCap,
  BookOpen,
  Building2,
  Users,
  Lightbulb,
  Database,
  Code,
  ChevronDown,
  ChevronUp,
  ArrowRight
} from 'lucide-react';

const milestones = [
  {
    year: '2023',
    title: 'Project Launch as Masters Thesis',
    description: 'Initial research phase and network analysis experimentation.'
  },
  {
    year: '2024',
    title: 'Masters Thesis Completion and Beginning of PhD',
    description: 'Gathering and digitizing historical transportation records & developing first modeling.'
  },
  {
    year: '2025',
    title: 'Proof-of-Concept & Data Collection',
    description: 'Developing modeling and analysis methodology for collected historical data.'
  },
  {
    year: '2026',
    title: 'Analysis Phase',
    description: 'Method selection & application, along with situation of transportation patterns in socio-political context.'
  },
  {
    year: '2027',
    title: 'Dissertation Completion',
    description: 'Finalizing research and presenting findings.'
  }
];

const AboutPage: React.FC = () => {
  const [showAcademicDetails, setShowAcademicDetails] = useState(false);

  return (
    <Layout>
      <div className="min-h-screen py-12">
        {/* Hero Section */}
        <div className="max-w-5xl mx-auto px-6 mb-16">
          <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20">
            <h1 className="text-4xl md:text-5xl font-bold text-white text-center mb-6">
              Rethinking the Past
            </h1>
            <p className="text-xl text-blue-100 text-center max-w-3xl mx-auto leading-relaxed">
              How digital history is transforming the way we understand, analyze, and experience historical knowledge
            </p>
          </div>
        </div>

        {/* Digital History Revolution */}
        <section className="max-w-5xl mx-auto px-6 mb-16">
          <div className="bg-gradient-to-br from-purple-600/90 to-indigo-600/90 rounded-xl p-8 shadow-2xl border border-purple-400/20">
            <div className="flex items-center mb-6">
              <Lightbulb className="h-8 w-8 text-purple-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">A New Way of Thinking About History</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <p className="text-lg text-purple-100 leading-relaxed">
                  Traditional history tells us what happened. Digital history shows us <em>how</em> it happened, 
                  <em>where</em> it happened, and <em>what if</em> it had happened differently.
                </p>
                <p className="text-lg text-purple-100 leading-relaxed">
                  By adding <strong>digitization</strong>, <strong>data modeling</strong>, and <strong>digital methods</strong> 
                  to historical research, we don't just change our tools—we change our entire hermeneutic process. 
                  We can ask new questions, see hidden patterns, and make discoveries that would be impossible with traditional methods alone.
                </p>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                <h3 className="text-xl font-semibold mb-4 text-white">Digital History Enables:</h3>
                <ul className="space-y-3 text-purple-100">
                  <li className="flex items-start">
                    <Database className="h-5 w-5 mr-2 mt-0.5 text-purple-300" />
                    <span>Interactive exploration of complex relationships</span>
                  </li>
                  <li className="flex items-start">
                    <Map className="h-5 w-5 mr-2 mt-0.5 text-purple-300" />
                    <span>Spatial and temporal analysis at scale</span>
                  </li>
                  <li className="flex items-start">
                    <Users className="h-5 w-5 mr-2 mt-0.5 text-purple-300" />
                    <span>Public engagement with historical research</span>
                  </li>
                  <li className="flex items-start">
                    <BarChart3 className="h-5 w-5 mr-2 mt-0.5 text-purple-300" />
                    <span>Pattern recognition across massive datasets</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* The Berlin Story */}
        <section className="max-w-5xl mx-auto px-6 mb-16">
          <div className="bg-gradient-to-br from-indigo-600/90 to-blue-600/90 rounded-xl p-8 shadow-2xl border border-indigo-400/20">
            <div className="flex items-center mb-6">
              <Building2 className="h-8 w-8 text-indigo-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">The Story of Connections</h2>
            </div>
            
            <div className="space-y-6">
              <p className="text-lg text-indigo-100 leading-relaxed">
                This project focuses on <strong>Berlin's public transportation</strong> not just as infrastructure, 
                but as a lens into <em>lived space</em>, <em>mobility</em>, and <em>time</em>. It's fundamentally 
                a story about <strong>connections</strong>—which neighborhoods were linked, which were isolated, 
                and how political ideologies shaped the very fabric of urban life.
              </p>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                  <h3 className="text-xl font-semibold mb-3 text-white">The Questions We're Exploring:</h3>
                  <ul className="space-y-2 text-indigo-100 text-sm">
                    <li>• West Berlin was isolated from the world—but were there areas isolated within the isolated city?</li>
                    <li>• How did different ideologies in East and West shape transport development?</li>
                    <li>• What if the Berlin Wall had never been erected? Which areas would be transport hubs today?</li>
                    <li>• How did people actually experience mobility and distance in a divided city?</li>
                  </ul>
                </div>
                
                <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                  <h3 className="text-xl font-semibold mb-3 text-white">Why It Matters Today:</h3>
                  <ul className="space-y-2 text-indigo-100 text-sm">
                    <li>• Understanding how politics shapes urban planning</li>
                    <li>• Learning from natural experiments in city development</li>
                    <li>• Applying historical insights to modern transport challenges</li>
                    <li>• Recognizing the human impact of infrastructure decisions</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Personal Journey */}
        <section className="max-w-5xl mx-auto px-6 mb-16">
          <div className="bg-gradient-to-br from-blue-600/90 to-cyan-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20">
            <div className="flex items-center mb-6">
              <GraduationCap className="h-8 w-8 text-blue-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">My Journey: Historian Meets Programmer</h2>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="md:col-span-2 space-y-4">
                <p className="text-lg text-blue-100 leading-relaxed">
                  I'm Noah, a PhD student operating on the cusp of <strong>history and data science</strong>. 
                  I'm fascinated by how practices from different domains can inform and strengthen each other.
                </p>
                <p className="text-lg text-blue-100 leading-relaxed">
                  My "aha moment" came during my final semester at <strong>King's College London</strong>, when I was 
                  challenged to create a digital edition of a document from the royal archives. I chose a 
                  17th-century Hanoverian state finance document and discovered how digital tools could not just 
                  preserve history, but make it accessible and understandable to the public in entirely new ways.
                </p>
                <p className="text-lg text-blue-100 leading-relaxed">
                  That experience set me on a path to combine my deep interest in programming—particularly 
                  <strong>data science and web development</strong>—with historical research. This project 
                  represents that intersection: rigorous historical methodology enhanced by modern computational approaches.
                </p>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                <h3 className="text-lg font-semibold mb-4 text-white">What I Bring:</h3>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <Book className="h-5 w-5 mr-2 text-blue-300" />
                    <span className="text-blue-100 text-sm">Historical Research</span>
                  </div>
                  <div className="flex items-center">
                    <Code className="h-5 w-5 mr-2 text-blue-300" />
                    <span className="text-blue-100 text-sm">Web Development</span>
                  </div>
                  <div className="flex items-center">
                    <Database className="h-5 w-5 mr-2 text-blue-300" />
                    <span className="text-blue-100 text-sm">Data Science</span>
                  </div>
                  <div className="flex items-center">
                    <Users className="h-5 w-5 mr-2 text-blue-300" />
                    <span className="text-blue-100 text-sm">Public History</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* What You'll Discover */}
        <section className="max-w-5xl mx-auto px-6 mb-16">
          <div className="bg-gradient-to-br from-cyan-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-cyan-400/20">
            <h2 className="text-3xl font-bold text-center mb-8 text-white">What You'll Discover Here</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="flex items-start">
                  <Map className="h-6 w-6 text-cyan-300 mr-3 mt-1" />
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">Interactive Visualizations</h3>
                    <p className="text-cyan-100">Explore Berlin's transport networks through time with interactive maps that reveal hidden patterns and connections.</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <BookOpen className="h-6 w-6 text-cyan-300 mr-3 mt-1" />
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">Behind-the-Scenes Articles</h3>
                    <p className="text-cyan-100">Deep dives into the tools, methods, and discoveries that power this research—from Neo4j to React to historical analysis.</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-6">
                <div className="flex items-start">
                  <Book className="h-6 w-6 text-cyan-300 mr-3 mt-1" />
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">Personal Reflections</h3>
                    <p className="text-cyan-100">Thoughts on cities, transport, technology, and the journey of learning to code as a historian.</p>
                  </div>
                </div>
                
                <div className="flex items-start">
                  <BarChart3 className="h-6 w-6 text-cyan-300 mr-3 mt-1" />
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">Current Work</h3>
                    <p className="text-cyan-100">Follow my latest projects, including Graph-RAG experiments and conference presentations exploring AI in historical research.</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="text-center mt-8">
              <Link 
                href="/visualizations" 
                className="inline-flex items-center px-8 py-3 bg-white text-cyan-600 rounded-lg hover:bg-cyan-50 transition-colors font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                Start Exploring
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* Academic Details - Collapsible */}
        <section className="max-w-5xl mx-auto px-6">
          <div className="bg-gradient-to-br from-gray-700/90 to-gray-600/90 rounded-xl shadow-2xl border border-gray-500/20">
            <button
              onClick={() => setShowAcademicDetails(!showAcademicDetails)}
              className="w-full p-6 flex items-center justify-between text-left hover:bg-white/5 transition-colors rounded-xl"
            >
              <h2 className="text-2xl font-bold text-white">Academic Details & Timeline</h2>
              {showAcademicDetails ? (
                <ChevronUp className="h-6 w-6 text-gray-300" />
              ) : (
                <ChevronDown className="h-6 w-6 text-gray-300" />
              )}
            </button>
            
            {showAcademicDetails && (
              <div className="p-6 pt-0 space-y-8">
                {/* Timeline */}
                <div>
                  <h3 className="text-xl font-semibold mb-6 text-white">Research Timeline</h3>
                  <div className="relative">
                    <div className="absolute left-0 md:left-1/2 h-full w-px bg-gray-500 transform -translate-x-1/2" />
                    
                    <div className="space-y-8">
                      {milestones.map((milestone, index) => (
                        <div 
                          key={index}
                          className={`relative flex ${
                            index % 2 === 0 ? 'md:flex-row-reverse' : 'md:flex-row'
                          } items-center`}
                        >
                          <div className="flex-1" />
                          <div className="absolute left-0 md:left-1/2 w-6 h-6 bg-blue-500 rounded-full transform -translate-x-1/2 flex items-center justify-center border-2 border-gray-700">
                            <Clock className="h-3 w-3 text-white" />
                          </div>
                          <div className="flex-1 ml-8 md:ml-0 md:px-6">
                            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600/30">
                              <div className="text-sm text-blue-400 font-semibold mb-1">
                                {milestone.year}
                              </div>
                              <h4 className="text-lg font-semibold mb-2 text-white">
                                {milestone.title}
                              </h4>
                              <p className="text-gray-300 text-sm">
                                {milestone.description}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Methods */}
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-xl font-semibold mb-4 text-white">Digital Methods</h3>
                    <ul className="space-y-2">
                      <li className="flex items-start">
                        <Database className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">Neo4j graph database for network analysis</span>
                      </li>
                      <li className="flex items-start">
                        <Map className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">GIS mapping of historical transportation networks</span>
                      </li>
                      <li className="flex items-start">
                        <BarChart3 className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">Interactive web visualizations with React</span>
                      </li>
                      <li className="flex items-start">
                        <Code className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">Python for data processing and analysis</span>
                      </li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-4 text-white">Traditional Methods</h3>
                    <ul className="space-y-2">
                      <li className="flex items-start">
                        <BookOpen className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">Archival research in Berlin institutions</span>
                      </li>
                      <li className="flex items-start">
                        <Book className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">Analysis of historical transport documents</span>
                      </li>
                      <li className="flex items-start">
                        <Users className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">Contextual historical analysis</span>
                      </li>
                      <li className="flex items-start">
                        <Building2 className="h-5 w-5 text-blue-400 mr-3 mt-1" />
                        <span className="text-gray-300">Urban planning and policy analysis</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Contact CTA */}
        <section className="max-w-3xl mx-auto px-6 py-16 text-center">
          <h2 className="text-2xl font-bold mb-6 text-white">Get Involved</h2>
          <p className="text-gray-300 mb-8 leading-relaxed">
            Whether you're an academic, a transport enthusiast, a programmer interested in history, 
            or simply curious about Berlin's story, I'd love to hear from you.
          </p>
          <div className="flex justify-center space-x-4">
            <Link 
              href="mailto:noah.baumann@yahoo.de"
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 hover:shadow-lg transform hover:-translate-y-1"
            >
              <Mail className="h-5 w-5 mr-2" />
              Contact Me
            </Link>
            <Link 
              href="/current-work"
              className="inline-flex items-center px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors border border-gray-600"
            >
              <Clock className="h-5 w-5 mr-2" />
              Current Work
            </Link>
          </div>
        </section>
      </div>
    </Layout>
  );
};

export default AboutPage;