import { useState } from 'react';
import Layout from '../../components/common/Layout';
import { 
  Bot, 
  Database, 
  MessageSquare, 
  Lightbulb, 
  Calendar, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Zap,
  Users,
  BookOpen,
  ArrowRight,
  Clock,
  Target,
  Wrench,
  GitBranch,
  Award,
  Globe,
  Code,
  Brain,
  Network,
  Layers,
  TestTube
} from 'lucide-react';

const monthlyUpdates = [
  {
    month: 'May-June 2025',
    title: 'Infrastructure & Question Taxonomy',
    status: 'in-progress',
    summary: 'Established evaluation framework foundations with Neo4j database setup and comprehensive question categorization for historical knowledge graphs.',
    details: 'Built infrastructure with Docker containers, MCP server configurations, and local LLM setup. Created 150+ categorized questions across factual, temporal, spatial, network, and historical query types. Established baseline implementations and ground truth datasets using pandas analysis of Berlin transport networks.',
    deliverables: ['Neo4j database with 13 historical snapshots', 'MCP server integration', '150+ evaluation questions', 'Docker setup for reproducibility']
  },
  {
    month: 'June-July 2025', 
    title: 'Traditional Graph-RAG Approaches',
    status: 'in-progress',
    summary: 'Implemented and evaluated three foundational Graph-RAG approaches: Query Generation, Vector-Based RAG, and Microsoft GraphRAG-inspired methods.',
    details: 'Developed natural language to Cypher translation with few-shot prompting, vector-based retrieval using graph-to-text conversion strategies, and hierarchical GraphRAG with community detection. Each approach tested against the evaluation dataset with performance benchmarking.',
    deliverables: ['Query Generation system (NL→Cypher)', 'Vector-based RAG implementation', 'Hybrid GraphRAG with community detection', 'Comparative performance analysis']
  },
  {
    month: 'July-August 2025',
    title: 'Agentic & MCP Integration',
    status: 'in-progress',
    summary: 'Pioneering agentic approaches with Model Context Protocol integration and specialized agent architectures for historical reasoning.',
    details: 'Currently implementing single-agent MCP systems and designing multi-agent architectures with specialized agents for temporal, spatial, network, and historical context analysis. This represents cutting-edge integration of 2025\'s "Year of AI Agents" trends with digital humanities methodology.',
    deliverables: ['Single-agent MCP implementation', 'Multi-agent architecture design', 'Specialized DH agents (Temporal, Spatial, Context)', 'MCP-Neo4j integration patterns']
  },
  {
    month: 'August-September 2025',
    title: 'Comprehensive Evaluation Framework',
    status: 'planned',
    summary: 'Complete evaluation across all five approaches with both quantitative metrics and qualitative assessment from the digital humanities community.',
    details: 'Systematic evaluation including factual accuracy, historical context integration, reasoning coherence, cost efficiency, and user experience. Beta testing with digital humanities researchers and development of automated evaluation pipelines.',
    deliverables: ['Automated evaluation pipeline', 'Performance benchmarks across approaches', 'DH community feedback integration', 'Cost-benefit analysis']
  },
  {
    month: 'September-November 2025',
    title: 'Open Source Toolkit Release',
    status: 'planned',
    summary: 'Launch the comprehensive DH-Graph-RAG Toolkit with documentation, guides, and community resources for widespread adoption.',
    details: 'Complete open source release including all five implementation approaches, evaluation framework, step-by-step setup guides for non-technical humanists, and community engagement infrastructure. Focus on making Graph-RAG accessible to the broader DH community.',
    deliverables: ['GitHub repository with full toolkit', 'Digital Humanist\'s Guide to Graph-RAG', 'PyPI package release', 'Community documentation website']
  }
];

const approaches = [
  {
    name: 'Query Generation',
    description: 'Natural language to Cypher translation',
    icon: MessageSquare,
    color: 'from-blue-500 to-cyan-500',
    details: 'Transforms historical questions into precise database queries using few-shot prompting and domain-specific examples.',
    bestFor: 'Factual queries, precise data retrieval, structured analysis'
  },
  {
    name: 'Vector-Based RAG',
    description: 'Embedding similarity retrieval',
    icon: Network,
    color: 'from-green-500 to-emerald-500',
    details: 'Converts graph structures to text representations, creates embeddings, and retrieves relevant context through similarity search.',
    bestFor: 'Exploratory queries, narrative responses, fuzzy matching'
  },
  {
    name: 'Hybrid GraphRAG',
    description: 'Microsoft-inspired hierarchical approach',
    icon: Layers,
    color: 'from-purple-500 to-violet-500',
    details: 'Combines community detection, multi-level summarization, and structured graph querying for complex analytical tasks.',
    bestFor: 'Complex analysis, pattern detection, multi-hop reasoning'
  },
  {
    name: 'Single-Agent MCP',
    description: 'Model Context Protocol integration',
    icon: Bot,
    color: 'from-orange-500 to-red-500',
    details: 'Uses standardized MCP for tool selection and execution, enabling dynamic query routing and adaptive responses.',
    bestFor: 'Tool orchestration, standardized workflows, API integration'
  },
  {
    name: 'Multi-Agent System',
    description: 'Specialized agent coordination',
    icon: Users,
    color: 'from-indigo-500 to-purple-500',
    details: 'Coordinates specialized agents for temporal, spatial, network, and historical analysis with sophisticated reasoning chains.',
    bestFor: 'Complex historical reasoning, multi-perspective analysis, nuanced insights'
  }
];

const deliverables = [
  {
    title: 'DH-Graph-RAG Toolkit',
    description: 'Open-source Materials for all approaches',
    icon: Wrench,
    features: ['Docker containers for easy setup', 'Step-by-step guides for non-technical users', 'Template configurations for different domains']
  },
  {
    title: 'Evaluation Framework',
    description: 'Systematic methodology for assessing Graph-RAG systems',
    icon: TestTube,
    features: ['Humanities-specific evaluation metrics', 'Automated benchmarking pipeline']
  },
  {
    title: 'Practical Implementation Guide',
    description: '"Graph-RAG for Digital Humanists" comprehensive resource',
    icon: BookOpen,
    features: ['When to use which approach', 'Common pitfalls and solutions']
  },
  {
    title: 'Working Implementation',
    description: 'Implementation of Graph-RAG System with Berlin Transport Networks',
    icon: Globe,
    features: ['Chatbot-based access to Knowledge Graph on Berlins Cold War Public Transport Network', 'Different impelementations tested and in-place for specific question types', 'Potential integration with map based visualizations']
  }
];

const GraphRAGPage: React.FC = () => {
  const [expandedUpdate, setExpandedUpdate] = useState<string | null>(null);
  const [expandedApproach, setExpandedApproach] = useState<string | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'from-green-600 to-emerald-600';
      case 'in-progress': return 'from-blue-600 to-cyan-600';
      case 'planned': return 'from-gray-600 to-gray-500';
      default: return 'from-gray-600 to-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✓';
      case 'in-progress': return '⏳';
      case 'planned': return '📅';
      default: return '❓';
    }
  };

  return (
    <Layout>
      <div className="py-12">
        {/* Hero Section */}
        <div className="max-w-6xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-purple-600/90 to-pink-600/90 rounded-xl p-8 shadow-2xl border border-purple-400/20">
            <div className="flex items-center mb-6">
              <Brain className="h-12 w-12 text-purple-200 mr-4" />
              <div>
                <h1 className="text-4xl md:text-5xl font-bold text-white">
                  Graph-RAG Evaluation Framework
                </h1>
                <p className="text-purple-200 text-lg mt-2">For Historical Knowledge Graphs</p>
              </div>
            </div>
            <p className="text-xl text-purple-100 leading-relaxed mb-6">
              Building a toolkit for digital humanists to evaluate and implement Graph-RAG systems. 
              Using Berlin's Cold War transport networks as a comprehensive case study to compare five distinct approaches 
              and create practical resources for the DH community.
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="flex items-center text-purple-200 bg-white/10 rounded-lg p-3 backdrop-blur-sm border border-white/20">
                <Target className="h-5 w-5 mr-2" />
                <span className="font-medium">Systematic Graph-RAG evaluation for humanities</span>
              </div>
              <div className="flex items-center text-purple-200 bg-white/10 rounded-lg p-3 backdrop-blur-sm border border-white/20">
                <Calendar className="h-5 w-5 mr-2" />
                <span className="font-medium">6-month project • Presenting first overview at DH2025, Lisbon</span>
              </div>
            </div>
          </div>
        </div>

        {/* Project Innovation */}
        <div className="max-w-6xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20">
            <div className="flex items-center mb-6">
              <Lightbulb className="h-8 w-8 text-blue-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">Why This Matters</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <p className="text-lg text-blue-100 leading-relaxed">
                  <strong>The Problem:</strong> Digital humanists have rich historical knowledge graphs and there is a lot of potential value in making them more accessible via natural language interfaces with the help of LLMs. However, there is a lack 
                  of guidance on how to implement this for humanities databases. Existing Graph-RAG approaches 
                  aren't evaluated for humanities use cases.
                </p>
                <p className="text-lg text-blue-100 leading-relaxed">
                  <strong>Our Solution:</strong> Compare five distinct approaches—from traditional query generation 
                  to cutting-edge agentic systems with Model Context Protocol—using Berlin's transport networks 
                  as a comprehensive test case.
                </p>
                <p className="text-lg text-blue-100 leading-relaxed">
                  <strong>The Impact:</strong> Create practical guidance that any digital humanities project 
                  can review to inform their implementation.
                </p>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                <h3 className="text-xl font-semibold mb-4 text-white">Project Uniqueness:</h3>
                <div className="space-y-4">
                  <div className="flex items-start">
                    <Award className="h-6 w-6 text-blue-300 mr-3 mt-1" />
                    <div>
                      <h4 className="font-semibold text-white">First Systematic Evaluation</h4>
                      <p className="text-blue-100 text-sm">Comprehensive comparison of 5 Graph-RAG approaches for historical data</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <Users className="h-6 w-6 text-blue-300 mr-3 mt-1" />
                    <div>
                      <h4 className="font-semibold text-white">Community-Centered Design</h4>
                      <p className="text-blue-100 text-sm">Built with and for digital humanists, not just technical researchers</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <Zap className="h-6 w-6 text-blue-300 mr-3 mt-1" />
                    <div>
                      <h4 className="font-semibold text-white">Cutting-Edge Integration</h4>
                      <p className="text-blue-100 text-sm">Incorporates 2025's agentic AI trends with MCP standardization</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Five Approaches */}
        <div className="max-w-6xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-indigo-600/90 to-blue-600/90 rounded-xl p-8 shadow-2xl border border-indigo-400/20">
            <div className="flex items-center mb-8">
              <GitBranch className="h-8 w-8 text-indigo-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">Five Graph-RAG Approaches Under Evaluation</h2>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {approaches.map((approach, index) => (
                <div key={index} className="bg-white/10 backdrop-blur-sm rounded-lg border border-white/20 p-6 hover:bg-white/15 transition-colors cursor-pointer"
                     onClick={() => setExpandedApproach(expandedApproach === approach.name ? null : approach.name)}>
                  <div className={`bg-gradient-to-r ${approach.color} rounded-full w-12 h-12 flex items-center justify-center mb-4`}>
                    <approach.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-white mb-2">{approach.name}</h3>
                  <p className="text-indigo-100 text-sm mb-3">{approach.description}</p>
                  
                  {expandedApproach === approach.name && (
                    <div className="border-t border-white/20 pt-3 mt-3">
                      <p className="text-indigo-100 text-sm mb-3">{approach.details}</p>
                      <div className="bg-white/5 rounded p-2">
                        <p className="text-indigo-200 text-xs font-medium">Best for: {approach.bestFor}</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center text-indigo-300 text-xs mt-2">
                    <span>Click for details</span>
                    {expandedApproach === approach.name ? (
                      <ChevronUp className="h-4 w-4 ml-1" />
                    ) : (
                      <ChevronDown className="h-4 w-4 ml-1" />
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <h3 className="text-xl font-semibold text-white mb-3">Evaluation Methodology</h3>
              <p className="text-indigo-100 mb-4">
                Each approach is tested against 150+ carefully categorized questions about Berlin's transport networks (1945-1989), 
                evaluating not just accuracy but historical context integration, reasoning quality, cost efficiency, and user experience.
              </p>
              <div className="grid md:grid-cols-5 gap-4 text-center">
                <div className="bg-white/5 rounded p-3">
                  <div className="text-indigo-300 font-semibold">Factual</div>
                  <div className="text-indigo-200 text-sm">Direct lookups</div>
                </div>
                <div className="bg-white/5 rounded p-3">
                  <div className="text-indigo-300 font-semibold">Temporal</div>
                  <div className="text-indigo-200 text-sm">Time-based analysis</div>
                </div>
                <div className="bg-white/5 rounded p-3">
                  <div className="text-indigo-300 font-semibold">Spatial</div>
                  <div className="text-indigo-200 text-sm">Geographic queries</div>
                </div>
                <div className="bg-white/5 rounded p-3">
                  <div className="text-indigo-300 font-semibold">Network</div>
                  <div className="text-indigo-200 text-sm">Graph structure</div>
                </div>
                <div className="bg-white/5 rounded p-3">
                  <div className="text-indigo-300 font-semibold">Historical</div>
                  <div className="text-indigo-200 text-sm">Context & impact</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Key Deliverables */}
        <div className="max-w-6xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-cyan-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-cyan-400/20">
            <div className="flex items-center mb-8">
              <Target className="h-8 w-8 text-cyan-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">Project Deliverables</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6">
              {deliverables.map((deliverable, index) => (
                <div key={index} className="bg-white/10 backdrop-blur-sm rounded-lg border border-white/20 p-6">
                  <div className="flex items-center mb-4">
                    <div className="bg-cyan-500/30 rounded-full w-10 h-10 flex items-center justify-center mr-3">
                      <deliverable.icon className="h-5 w-5 text-cyan-200" />
                    </div>
                    <h3 className="font-semibold text-white">{deliverable.title}</h3>
                  </div>
                  <p className="text-cyan-100 mb-4">{deliverable.description}</p>
                  <ul className="space-y-1">
                    {deliverable.features.map((feature, i) => (
                      <li key={i} className="text-cyan-200 text-sm flex items-center">
                        <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full mr-2"></div>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Monthly Timeline */}
        <div className="max-w-6xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-violet-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-violet-400/20">
            <div className="flex items-center mb-8">
              <Clock className="h-8 w-8 text-violet-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">Development Timeline & Progress</h2>
            </div>
            
            <div className="space-y-4">
              {monthlyUpdates.map((update, index) => (
                <div key={index} className="bg-white/10 backdrop-blur-sm rounded-lg border border-white/20 overflow-hidden">
                  <button
                    onClick={() => setExpandedUpdate(expandedUpdate === update.month ? null : update.month)}
                    className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center">
                      <div className={`bg-gradient-to-r ${getStatusColor(update.status)} rounded-full w-8 h-8 flex items-center justify-center mr-4 text-white text-sm font-bold`}>
                        {getStatusIcon(update.status)}
                      </div>
                      <div className="text-left">
                        <h3 className="font-semibold text-white">{update.month}: {update.title}</h3>
                        <p className="text-violet-100 text-sm">{update.summary}</p>
                      </div>
                    </div>
                    {expandedUpdate === update.month ? (
                      <ChevronUp className="h-5 w-5 text-violet-300" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-violet-300" />
                    )}
                  </button>
                  
                  {expandedUpdate === update.month && (
                    <div className="px-4 pb-4 border-t border-white/10">
                      <p className="text-violet-100 leading-relaxed pt-4 mb-4">{update.details}</p>
                      {update.deliverables && (
                        <div>
                          <h4 className="font-semibold text-white mb-2">Key Deliverables:</h4>
                          <ul className="space-y-1">
                            {update.deliverables.map((deliverable, i) => (
                              <li key={i} className="text-violet-200 text-sm flex items-center">
                                <div className="w-1.5 h-1.5 bg-violet-400 rounded-full mr-2"></div>
                                {deliverable}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Case Study Preview */}
        <div className="max-w-6xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-emerald-600/90 to-cyan-600/90 rounded-xl p-8 shadow-2xl border border-emerald-400/20">
            <div className="flex items-center mb-6">
              <Database className="h-8 w-8 text-emerald-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">Berlin Transport Networks: The Perfect Test Case</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <p className="text-lg text-emerald-100 leading-relaxed">
                  Berlin's Cold War transport system (1945-1989) provides an ideal testing ground with complex 
                  temporal, geographical, and political dimensions. The dataset captures both technical developments 
                  and Cold War political realities.
                </p>
                <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20">
                  <h3 className="font-semibold text-white mb-3">Dataset Complexity:</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-emerald-300 font-semibold">13 Time Snapshots</div>
                      <div className="text-emerald-200">1945-1989 evolution</div>
                    </div>
                    <div>
                      <div className="text-emerald-300 font-semibold">Multi-Modal Transport</div>
                      <div className="text-emerald-200">Tram, U-Bahn, S-Bahn, Bus</div>
                    </div>
                    <div>
                      <div className="text-emerald-300 font-semibold">Political Division</div>
                      <div className="text-emerald-200">East/West administrative split</div>
                    </div>
                    <div>
                      <div className="text-emerald-300 font-semibold">Geographic Layers</div>
                      <div className="text-emerald-200">Districts, postal codes, boundaries</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-600/30">
                <h3 className="font-semibold text-white mb-4">Example Research Questions:</h3>
                <div className="space-y-3 text-sm">
                  <div className="bg-emerald-600/20 rounded-lg p-3 text-emerald-100">
                    <strong>Temporal:</strong> "How did tram networks change in East Berlin from 1960-1980?"
                  </div>
                  <div className="bg-emerald-600/20 rounded-lg p-3 text-emerald-100">
                    <strong>Spatial:</strong> "Which stations were within 2km of Checkpoint Charlie?"
                  </div>
                  <div className="bg-emerald-600/20 rounded-lg p-3 text-emerald-100">
                    <strong>Historical:</strong> "How did the Berlin Wall affect transport accessibility for divided families?"
                  </div>
                  <div className="bg-emerald-600/20 rounded-lg p-3 text-emerald-100">
                    <strong>Network:</strong> "What alternative routes existed between East and West after 1961?"
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Community Impact & Future */}
        <div className="max-w-6xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-rose-600/90 to-orange-600/90 rounded-xl p-8 shadow-2xl border border-rose-400/20">
            <div className="flex items-center mb-6">
              <Globe className="h-8 w-8 text-rose-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">Beyond Berlin: Community Impact</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <p className="text-lg text-rose-100 leading-relaxed">
                  This project creates reusable infrastructure that any digital humanities project can adopt. 
                  The evaluation framework, implementation guides, and community resources will benefit 
                  researchers working with historical knowledge graphs across domains.
                </p>
                <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20">
                  <h3 className="font-semibold text-white mb-2">Potential Applications:</h3>
                  <ul className="text-rose-100 text-sm space-y-1">
                    <li>• Medieval trade networks and economic history</li>
                    <li>• Social network analysis in historical correspondence</li>
                    <li>• Urban development and architectural heritage</li>
                    <li>• Migration patterns and demographic change</li>
                    <li>• Cultural institution networks and collaboration</li>
                  </ul>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-white">Open Source Commitment</h3>
                <p className="text-rose-100">
                  All components will be released under open licenses with comprehensive documentation, 
                  tutorial materials, and community support infrastructure.
                </p>
                <div className="flex flex-col gap-3">
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 border border-white/20">
                    <div className="flex items-center">
                      <Code className="h-5 w-5 text-rose-300 mr-2" />
                      <span className="text-white font-medium">GitHub Repository</span>
                    </div>
                    <p className="text-rose-200 text-sm mt-1">Complete toolkit with Docker setup</p>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 border border-white/20">
                    <div className="flex items-center">
                      <BookOpen className="h-5 w-5 text-rose-300 mr-2" />
                      <span className="text-white font-medium">Documentation Site</span>
                    </div>
                    <p className="text-rose-200 text-sm mt-1">Tutorials and implementation guides</p>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 border border-white/20">
                    <div className="flex items-center">
                      <Users className="h-5 w-5 text-rose-300 mr-2" />
                      <span className="text-white font-medium">Community Support</span>
                    </div>
                    <p className="text-rose-200 text-sm mt-1">Workshops and collaborative development</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-6 text-white">Follow the Development</h2>
          <p className="text-gray-300 mb-8 leading-relaxed text-lg">
            This project represents a significant methodological contribution to digital humanities, 
            creating the first systematic evaluation framework for Graph-RAG systems with historical knowledge graphs. 
            Follow along as we build practical infrastructure for the community.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="/current-work/conferences"
              className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 hover:shadow-xl transform hover:-translate-y-1 text-lg"
            >
              <Calendar className="h-6 w-6 mr-3" />
              DH2025 Conference Details
              <ArrowRight className="h-5 w-5 ml-2" />
            </a>
            <a 
              href="/blog"
              className="inline-flex items-center px-8 py-4 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors border border-gray-600 text-lg"
            >
              <BookOpen className="h-6 w-6 mr-3" />
              Read Development Updates
            </a>
          </div>
          
          <div className="mt-8 text-gray-400 text-sm">
            <p>Open source release planned for May 2025 • Community workshops throughout development</p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default GraphRAGPage;