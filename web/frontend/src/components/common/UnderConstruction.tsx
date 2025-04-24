// components/common/UnderConstruction.tsx
import React from 'react';
import Link from 'next/link';
import { Construction, ArrowLeft, Mail } from 'lucide-react';

interface UnderConstructionProps {
  title?: string;
  expectedDate?: string;
  contactEmail?: string;
}

const UnderConstruction: React.FC<UnderConstructionProps> = ({
  title = "Page Under Development",
  expectedDate = "early 2024",
  contactEmail = "research@berlintransport.org"
}) => {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-sm border p-8 text-center">
        <Construction className="w-16 h-16 mx-auto text-blue-600 mb-6" />
        
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          {title}
        </h1>
        
        <div className="space-y-4 text-gray-600">
          <p>
            This section of the Berlin Transport Project is currently under development 
            and will be available in {expectedDate}.
          </p>
          
          <p>
            In the meantime, you might be interested in:
          </p>
          
          <ul className="text-left max-w-md mx-auto space-y-2 mb-6">
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 bg-blue-600 rounded-full"></span>
              <Link href="/visualizations" className="text-blue-600 hover:underline">
                Exploring our interactive visualizations
              </Link>
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 bg-blue-600 rounded-full"></span>
              <Link href="/blog" className="text-blue-600 hover:underline">
                Reading our latest blog posts
              </Link>
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 bg-blue-600 rounded-full"></span>
              <Link href="/articles" className="text-blue-600 hover:underline">
                Viewing our published articles
              </Link>
            </li>
          </ul>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
            <Link 
              href="/"
              className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Return Home
            </Link>
            
            <a 
              href={`mailto:${contactEmail}`}
              className="inline-flex items-center justify-center px-4 py-2 border border-blue-600 rounded-md text-blue-600 bg-white hover:bg-blue-50 transition-colors"
            >
              <Mail className="w-4 h-4 mr-2" />
              Contact Research Team
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnderConstruction;