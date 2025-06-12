import Layout from '@/components/common/Layout';

const PrivacyPolicy = () => {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="bg-gradient-to-br from-green-600/90 to-blue-600/90 rounded-xl p-8 shadow-2xl border border-green-400/20 mb-8">
          <h1 className="text-3xl font-bold text-white mb-4">Privacy Policy</h1>
        </div>
        
        {/* Content */}
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 shadow-2xl border border-white/20">
          <div className="prose prose-lg max-w-none prose-invert prose-headings:text-white prose-p:text-gray-200 prose-a:text-blue-300 prose-a:hover:text-blue-200 prose-strong:text-white prose-li:text-gray-200 prose-ul:text-gray-200">
            <section className="mb-8">
              <h2 className="text-white">Data Collection and Usage</h2>
              <p>The Berlin Transport Project ("we," "us," or "our") collects limited data to improve user experience and support research. This includes:</p>
              <ul>
                <li>Technical data (browser type, device information)</li>
                <li>Usage data (pages visited, interaction with visualizations)</li>
                <li>Optional account information for researchers</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-white">Research Data Usage</h2>
              <p>As an academic research project at Humboldt University of Berlin, we may use anonymized usage data for:</p>
              <ul>
                <li>Academic research purposes</li>
                <li>Improving our visualization tools</li>
                <li>Understanding user interaction patterns</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-white">Data Protection</h2>
              <p>We follow GDPR guidelines and implement appropriate security measures to protect your data. Our data protection practices include:</p>
              <ul>
                <li>Data encryption in transit and at rest</li>
                <li>Regular security audits</li>
                <li>Limited data retention periods</li>
                <li>Restricted access to personal information</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-white">Your Rights</h2>
              <p>Under GDPR, you have the right to:</p>
              <ul>
                <li>Access your personal data</li>
                <li>Request data correction or deletion</li>
                <li>Withdraw consent for data processing</li>
                <li>Request data portability</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-white">Contact</h2>
              <p>For privacy-related inquiries, please contact our data protection officer at:</p>
              <p>Email: <a href="mailto:noah.baumann@yahoo.de" className="text-blue-300 hover:text-blue-200">noah.baumann@yahoo.de</a></p>
            </section>

            <p className="text-sm text-gray-400 mt-8">Last updated: January 2025</p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default PrivacyPolicy;
