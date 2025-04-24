// pages/about.tsx
import { useState } from 'react';
import Link from 'next/link';
import Layout from '../components/common/Layout';
import { 
  Book, 
  ChartBar, 
  Mail, 
  Clock, 
  Map, 
  GraduationCap,
  BookOpen,
  Building2,
  Users
} from 'lucide-react';

const milestones = [
  {
    year: '2023',
    title: 'Project Launch as Masters Thesis',
    description: 'Initial research phase and network analysis experimentation.'
  },
  {
    year: '2024',
    title: 'Masters Thesis Completeion and beginning of PhD',
    description: 'Gathering and digitizing historical transportation records & developing first modeling.'
  },
  {
    year: '2025',
    title: 'Proof-of-Concept & Data Collection',
    description: 'Developing modelling and analysis methodology for collected historical data.'
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
  const [activeSection, setActiveSection] = useState('');

  return (
    <Layout>
      <div className="min-h-screen">
        {/* Hero Section */}
        <div className="mt-8">
          <div className="max-w-5xl mx-auto px-6">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 text-center mb-6">
              About This Project
            </h1>
            <p className="text-xl text-gray-600 text-center max-w-3xl mx-auto">
              Exploring Berlin's transportation history through digital methods and historical analysis.
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-5xl mx-auto px-6 py-12">
          {/* Project Overview */}
          <section className="mb-16">
            <div className="prose prose-lg max-w-none">
              <p className="lead">
                This research project, conducted at the Digital History Department of 
                Humboldt-Universität zu Berlin, examines how Berlin's public transportation 
                systems shaped urban life during critical periods of the city's history.
              </p>
            </div>
          </section>

          {/* Key Features */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-8">Project Components</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  icon: <BookOpen className="h-6 w-6" />,
                  title: "Databases",
                  description: "Digitized historical records and transportation data"
                },
                {
                  icon: <ChartBar className="h-6 w-6" />,
                  title: "Visualizations",
                  description: "Interactive maps and data visualizations"
                },
                {
                  icon: <Book className="h-6 w-6" />,
                  title: "Research Articles",
                  description: "Regular updates on findings and methodologies"
                }
              ].map((feature, index) => (
                <div 
                  key={index}
                  className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
                >
                  <div className="text-blue-600 mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Timeline */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-8">Project Timeline</h2>
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-0 md:left-1/2 h-full w-px bg-gray-200 transform -translate-x-1/2" />
              
              {/* Timeline items */}
              <div className="space-y-12">
                {milestones.map((milestone, index) => (
                  <div 
                    key={index}
                    className={`relative flex ${
                      index % 2 === 0 ? 'md:flex-row-reverse' : 'md:flex-row'
                    } items-center`}
                  >
                    <div className="flex-1" />
                    <div className="absolute left-0 md:left-1/2 w-8 h-8 bg-blue-600 rounded-full transform -translate-x-1/2 flex items-center justify-center">
                      <Clock className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1 ml-12 md:ml-0 md:px-8">
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <div className="text-sm text-blue-600 font-semibold mb-1">
                          {milestone.year}
                        </div>
                        <h3 className="text-lg font-semibold mb-2">
                          {milestone.title}
                        </h3>
                        <p className="text-gray-600">
                          {milestone.description}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Research Methods */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-8">Research Methods</h2>
            <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-100">
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-xl font-semibold mb-4">Digital Approaches</h3>
                  <ul className="space-y-3">
                    <li className="flex items-start">
                      <Map className="h-5 w-5 text-blue-600 mr-3 mt-1" />
                      <span>GIS mapping of historical transportation networks</span>
                    </li>
                    <li className="flex items-start">
                      <ChartBar className="h-5 w-5 text-blue-600 mr-3 mt-1" />
                      <span>Network analysis of transportation patterns</span>
                    </li>
                    <li className="flex items-start">
                      <Building2 className="h-5 w-5 text-blue-600 mr-3 mt-1" />
                      <span>Urban development pattern analysis</span>
                    </li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-4">Traditional Methods</h3>
                  <ul className="space-y-3">
                    <li className="flex items-start">
                      <BookOpen className="h-5 w-5 text-blue-600 mr-3 mt-1" />
                      <span>Archival research</span>
                    </li>
                    <li className="flex items-start">
                      <Users className="h-5 w-5 text-blue-600 mr-3 mt-1" />
                      <span>Close-reading of historical source materials</span>
                    </li>
                    <li className="flex items-start">
                      <GraduationCap className="h-5 w-5 text-blue-600 mr-3 mt-1" />
                      <span>Historical analysis and interpretation</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Contact Section */}
          <section className="text-center">
            <h2 className="text-2xl font-bold mb-6">Get Involved</h2>
            <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
              Whether you're an academic, a transport enthusiast, or simply interested 
              in Berlin's history, your insights can contribute to this research.
            </p>
            <div className="flex justify-center space-x-4">
              <Link 
                href="mailto:noah.baumann@yahoo.de"
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Mail className="h-5 w-5 mr-2" />
                Contact
              </Link>
              <Link 
                href="/articles"
                className="inline-flex items-center px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Book className="h-5 w-5 mr-2" />
                Read Articles
              </Link>
            </div>
          </section>
        </div>
      </div>
    </Layout>
  );
};

export default AboutPage;