import { useState } from 'react';
import Layout from '../../components/common/Layout';
import { 
  Calendar,
  MapPin,
  ExternalLink,
  Clock,
  Users,
  Presentation,
  FileText,
  ArrowRight,
  Globe,
  Award,
  ChevronDown,
  ChevronUp,
  Lightbulb
} from 'lucide-react';

interface Conference {
  id: string;
  title: string;
  fullName: string;
  date: string;
  dateRange: string;
  location: string;
  format: string;
  website: string;
  theme?: string;
  organizers: string[];
  presentations: Presentation[];
  description: string;
  status: 'upcoming' | 'completed';
}

interface Presentation {
  title: string;
  format: 'poster' | 'talk' | 'pitch' | 'online-presentation';
  time?: string;
  description: string;
  focus: string;
  slidesUrl?: string;
  posterUrl?: string;
  blogPostUrl?: string;
}

const conferences: Conference[] = [
  {
    id: 'sunbelt2025',
    title: 'Sunbelt 2025',
    fullName: 'International Social Network Conference - Sunbelt 2025',
    date: 'June 24, 2025',
    dateRange: 'June 23-29, 2025',
    location: 'Paris, France (Online Presentation)',
    format: 'Online Oral Presentation',
    website: 'https://sunbelt2025.org/',
    theme: 'Social Networks, Mechanisms, and Algorithms',
    organizers: ['International Network for Social Network Analysis (INSNA)', 'Sorbonne University', 'Sciences Po'],
    status: 'upcoming',
    description: 'The largest international conference for social network analysis, bringing together researchers from sociology, computer science, mathematics, and related fields.',
    presentations: [
      {
        title: 'Multi-level Administrative Boundaries in Dynamic Network Analysis: Modeling Berlin\'s Public Transportation System (1945-1989)',
        format: 'online-presentation',
        time: '1:00pm - 1:20pm (Session ID: 373 / ON-13: 4)',
        description: 'Introducing a novel approach to analyzing transportation networks by incorporating multiple levels of changing administrative boundaries using Neo4j multilayer networks.',
        focus: 'Technical methodology and temporal network modeling approaches for historical transport data.'
      }
    ]
  },
  {
    id: 'dh2025',
    title: 'DH2025',
    fullName: 'Digital Humanities Conference 2025',
    date: 'July 14-18, 2025',
    dateRange: 'July 14-18, 2025',
    location: 'Lisbon, Portugal',
    format: 'In-Person Conference',
    website: 'https://dh2025.adho.org/',
    theme: 'Building access and accessibility, open science to all citizens',
    organizers: ['Alliance of Digital Humanities Organizations (ADHO)'],
    status: 'upcoming',
    description: 'The premier international conference for digital humanities, focusing on accessibility, citizenship, and open science approaches.',
    presentations: [
      {
        title: 'Temporal Methodologies for Infrastructure Analysis: Berlin\'s Transportation Network During the Cold War',
        format: 'talk',
        description: 'Addressing methodological challenges in modeling temporal change within digital humanities, comparing snapshot-based vs. geographic node-merger techniques.',
        focus: 'Digital humanities methodology, temporal modeling paradigms, and FAIR data principles.'
      },
      {
        title: 'Citizen Science and RAG Innovation in Historical Transport Database',
        format: 'poster',
        description: 'Presenting an innovative application of citizen science methodologies and Retrieval-Augmented Generation (RAG) to enhance a graph database of Berlin\'s Cold War transport system.',
        focus: 'Public engagement, crowdsourcing, and AI integration in digital humanities research.'
      }
    ]
  },
  {
    id: 'historikertag2025',
    title: 'Historikertag 2025',
    fullName: '55. Deutscher Historikertag',
    date: 'September 16-19, 2025',
    dateRange: 'September 16-19, 2025',
    location: 'Bonn, Germany',
    format: 'In-Person Conference',
    website: 'https://www.historikertag.de/Bonn2025/',
    theme: 'Dynamiken der Macht (Dynamics of Power)',
    organizers: ['Verband der Historiker und Historikerinnen Deutschlands (VHD)'],
    status: 'upcoming',
    description: 'The largest platform for German-speaking historians, one of the biggest humanities conferences in Europe with approximately 3,000 participants.',
    presentations: [
      {
        title: 'Pitch für Peter-Haber-Preis für digitale Geschichtswissenschaft 2025',
        format: 'pitch',
        description: 'Presenting the PhD project on Berlin\'s Cold War transport system with focus on historical insights and urban development patterns.',
        focus: 'Historical insights, urban mobility patterns, and the human impact of political divisions on daily life.'
      },
      {
        title: 'Wandel verstehen: Eine dynamische Netzwerkanalyse des Berliner öffentlichen Nahverkehrs (1945-1989)',
        format: 'poster',
        description: 'Poster presentation competing for a research prize, emphasizing historical discoveries and their significance for urban history.',
        focus: 'Historical analysis, political geography\'s impact on urban infrastructure, and lessons for contemporary cities.'
      }
    ]
  }
];

const ConferencesPage: React.FC = () => {
  const [expandedConference, setExpandedConference] = useState<string | null>(null);

  const toggleConference = (id: string) => {
    setExpandedConference(expandedConference === id ? null : id);
  };

  const formatIcon = (format: string) => {
    switch (format) {
      case 'poster': return <FileText className="h-4 w-4" />;
      case 'talk': return <Presentation className="h-4 w-4" />;
      case 'pitch': return <Lightbulb className="h-4 w-4" />;
      case 'online-presentation': return <Globe className="h-4 w-4" />;
      default: return <Presentation className="h-4 w-4" />;
    }
  };

  return (
    <Layout>
      <div className="py-12">
        {/* Hero Section */}
        <div className="max-w-5xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20 text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Conferences & Presentations
            </h1>
            <p className="text-xl text-blue-100 max-w-3xl mx-auto leading-relaxed">
              Sharing research on digital history, temporal network analysis, and Berlin's transport heritage 
              at international conferences
            </p>
          </div>
        </div>

        {/* Conference Overview */}
        <div className="max-w-5xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-purple-600/90 to-indigo-600/90 rounded-xl p-8 shadow-2xl border border-purple-400/20">
            <div className="flex items-center mb-6">
              <Users className="h-8 w-8 text-purple-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">2025 Conference Schedule</h2>
            </div>
            <p className="text-lg text-purple-100 leading-relaxed mb-6">
              This year brings exciting opportunities to present my research on Berlin's Cold War transport system 
              across three major international conferences, each with a different focus and audience.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6">
              {conferences.map((conf, index) => (
                <div key={conf.id} className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20">
                  <h3 className="text-lg font-semibold text-white mb-2">{conf.title}</h3>
                  <div className="flex items-center text-purple-100 text-sm mb-2">
                    <Calendar className="h-4 w-4 mr-2" />
                    {conf.date}
                  </div>
                  <div className="flex items-center text-purple-100 text-sm mb-3">
                    <MapPin className="h-4 w-4 mr-2" />
                    {conf.location}
                  </div>
                  <p className="text-purple-100 text-sm">{conf.presentations.length} presentation{conf.presentations.length > 1 ? 's' : ''}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Detailed Conference Listings */}
        <div className="max-w-5xl mx-auto px-6 space-y-8">
          {conferences.map((conference, index) => (
            <div key={conference.id} className="bg-gradient-to-br from-indigo-600/90 to-blue-600/90 rounded-xl shadow-2xl border border-indigo-400/20 overflow-hidden">
              {/* Conference Header */}
              <div className="p-8">
                <div className="flex items-start justify-between mb-6">
                  <div className="flex-1">
                    <h2 className="text-3xl font-bold text-white mb-2">{conference.fullName}</h2>
                    <div className="flex flex-wrap gap-4 text-indigo-100 mb-4">
                      <div className="flex items-center">
                        <Calendar className="h-5 w-5 mr-2" />
                        {conference.dateRange}
                      </div>
                      <div className="flex items-center">
                        <MapPin className="h-5 w-5 mr-2" />
                        {conference.location}
                      </div>
                      {conference.theme && (
                        <div className="flex items-center">
                          <Award className="h-5 w-5 mr-2" />
                          {conference.theme}
                        </div>
                      )}
                    </div>
                  </div>
                  <a 
                    href={conference.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Conference Website
                  </a>
                </div>

                <p className="text-indigo-100 leading-relaxed mb-6">{conference.description}</p>

                {/* Presentations */}
                <div className="space-y-4">
                  {conference.presentations.map((presentation, pIndex) => (
                    <div key={pIndex} className="bg-white/10 backdrop-blur-sm p-6 rounded-lg border border-white/20">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center mb-2">
                            {formatIcon(presentation.format)}
                            <span className="ml-2 text-sm text-indigo-200 capitalize font-medium">
                              {presentation.format.replace('-', ' ')}
                            </span>
                            {presentation.time && (
                              <>
                                <span className="mx-2 text-indigo-300">•</span>
                                <Clock className="h-4 w-4 mr-1 text-indigo-200" />
                                <span className="text-sm text-indigo-200">{presentation.time}</span>
                              </>
                            )}
                          </div>
                          <h3 className="text-xl font-semibold text-white mb-3">
                            {presentation.title}
                          </h3>
                          <p className="text-indigo-100 leading-relaxed mb-3">
                            {presentation.description}
                          </p>
                          <div className="bg-blue-900/30 p-3 rounded border border-blue-400/20">
                            <h4 className="text-sm font-semibold text-blue-200 mb-1">Focus:</h4>
                            <p className="text-sm text-blue-100">{presentation.focus}</p>
                          </div>
                        </div>
                      </div>

                      {/* Placeholder links for materials */}
                      <div className="flex flex-wrap gap-2 mt-4">
                        {presentation.format === 'poster' && (
                          <span className="px-3 py-1 bg-gray-600/50 text-gray-300 rounded text-sm">
                            Poster: Coming after conference
                          </span>
                        )}
                        {(presentation.format === 'talk' || presentation.format === 'online-presentation') && (
                          <span className="px-3 py-1 bg-gray-600/50 text-gray-300 rounded text-sm">
                            Slides: Coming after conference
                          </span>
                        )}
                        <span className="px-3 py-1 bg-gray-600/50 text-gray-300 rounded text-sm">
                          Blog post: Coming after conference
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Conference Details - Collapsible */}
                <button
                  onClick={() => toggleConference(conference.id)}
                  className="w-full mt-6 p-4 bg-white/10 hover:bg-white/15 rounded-lg border border-white/20 transition-colors flex items-center justify-between"
                >
                  <span className="text-white font-medium">Conference Details & Organizers</span>
                  {expandedConference === conference.id ? (
                    <ChevronUp className="h-5 w-5 text-white" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-white" />
                  )}
                </button>

                {expandedConference === conference.id && (
                  <div className="mt-4 p-4 bg-white/10 rounded-lg border border-white/20">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-white mb-3">Organizers</h4>
                        <ul className="space-y-1 text-indigo-100">
                          {conference.organizers.map((org, oIndex) => (
                            <li key={oIndex} className="text-sm">• {org}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold text-white mb-3">Format</h4>
                        <p className="text-indigo-100 text-sm">{conference.format}</p>
                        {conference.theme && (
                          <>
                            <h4 className="font-semibold text-white mb-1 mt-3">Theme</h4>
                            <p className="text-indigo-100 text-sm">{conference.theme}</p>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Follow Updates */}
        <div className="max-w-3xl mx-auto px-6 py-16 text-center">
          <h2 className="text-2xl font-bold mb-6 text-white">Follow Along</h2>
          <p className="text-gray-300 mb-8 leading-relaxed">
            I'll be sharing updates, reflections, and materials from each conference through blog posts. 
            Each presentation offers a different perspective on the intersection of digital history, 
            network analysis, and public engagement.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="/blog"
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 hover:shadow-lg transform hover:-translate-y-1"
            >
              <ArrowRight className="h-5 w-5 mr-2" />
              Read Conference Blog Posts
            </a>
            <a 
              href="/current-work/graph-rag"
              className="inline-flex items-center px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors border border-gray-600"
            >
              <Lightbulb className="h-5 w-5 mr-2" />
              Current Research Projects
            </a>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ConferencesPage;