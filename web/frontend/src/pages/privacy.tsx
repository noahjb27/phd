// pages/privacy.tsx
import Layout from '@/components/common/Layout';

const PrivacyPolicy = () => {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>
        
        <div className="prose prose-gray max-w-none">
          <section className="mb-8">
            <h2>Data Collection and Usage</h2>
            <p>The Berlin Transport Project ("we," "us," or "our") collects limited data to improve user experience and support research. This includes:</p>
            <ul>
              <li>Technical data (browser type, device information)</li>
              <li>Usage data (pages visited, interaction with visualizations)</li>
              <li>Optional account information for researchers</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2>Research Data Usage</h2>
            <p>As an academic research project at Humboldt University of Berlin, we may use anonymized usage data for:</p>
            <ul>
              <li>Academic research purposes</li>
              <li>Improving our visualization tools</li>
              <li>Understanding user interaction patterns</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2>Data Protection</h2>
            <p>We follow GDPR guidelines and implement appropriate security measures to protect your data. Our data protection practices include:</p>
            <ul>
              <li>Data encryption in transit and at rest</li>
              <li>Regular security audits</li>
              <li>Limited data retention periods</li>
              <li>Restricted access to personal information</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2>Your Rights</h2>
            <p>Under GDPR, you have the right to:</p>
            <ul>
              <li>Access your personal data</li>
              <li>Request data correction or deletion</li>
              <li>Withdraw consent for data processing</li>
              <li>Request data portability</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2>Contact</h2>
            <p>For privacy-related inquiries, please contact our data protection officer at:</p>
            <p>Email: noah.baumann@yahoo.de</p>
          </section>

          <p className="text-sm text-gray-500 mt-8">Last updated: January 2025</p>
        </div>
      </div>
    </Layout>
  );
};

export default PrivacyPolicy;