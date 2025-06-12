// pages/terms.tsx
import Layout from '@/components/common/Layout';

const TermsOfUse = () => {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="bg-gradient-to-br from-purple-600/90 to-pink-600/90 rounded-xl p-8 shadow-2xl border border-purple-400/20 mb-8">
          <h1 className="text-3xl font-bold text-white mb-4">Terms of Use</h1>
        </div>
        
        {/* Content */}
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 shadow-2xl border border-white/20">
          <div className="prose prose-lg max-w-none prose-invert prose-headings:text-white prose-p:text-gray-200 prose-a:text-blue-300 prose-a:hover:text-blue-200 prose-strong:text-white prose-li:text-gray-200 prose-ul:text-gray-200">
            <section className="mb-8">
              <h2 className="text-white">Academic Use</h2>
              <p>The Berlin Transport Project is an academic research project. By using this website, you agree to:</p>
              <ul>
                <li>Use content for academic and research purposes</li>
                <li>Properly cite the project when using our data or visualizations</li>
                <li>Not use the content for commercial purposes without permission</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-white">Data Usage</h2>
              <p>Our historical transportation data is provided under the following terms:</p>
              <ul>
                <li>Data may be used for research and educational purposes</li>
                <li>Attribution is required for any published work using our data</li>
                <li>Modifications to data must be clearly documented</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-white">User Accounts</h2>
              <p>User accounts are subject to:</p>
              <ul>
                <li>Registration of User Interest</li>
                <li>Regular review of account activity</li>
              </ul>
            </section>

            <p className="text-sm text-gray-400 mt-8">Last updated: January 2025</p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default TermsOfUse;