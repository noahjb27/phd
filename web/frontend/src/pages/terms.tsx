// pages/terms.tsx
import Layout from '@/components/common/Layout';

const TermsOfUse = () => {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8">Terms of Use</h1>
        
        <div className="prose prose-gray max-w-none">
          <section className="mb-8">
            <h2>Academic Use</h2>
            <p>The Berlin Transport Project is an academic research project. By using this website, you agree to:</p>
            <ul>
              <li>Use content for academic and research purposes</li>
              <li>Properly cite the project when using our data or visualizations</li>
              <li>Not use the content for commercial purposes without permission</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2>Data Usage</h2>
            <p>Our historical transportation data is provided under the following terms:</p>
            <ul>
              <li>Data may be used for research and educational purposes</li>
              <li>Attribution is required for any published work using our data</li>
              <li>Modifications to data must be clearly documented</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2>User Accounts</h2>
            <p>User accounts are subject to:</p>
            <ul>
              <li>Registration of User Interest</li>
              <li>Regular review of account activity</li>
            </ul>
          </section>

          <p className="text-sm text-gray-500 mt-8">Last updated: January 2025</p>
        </div>
      </div>
    </Layout>
  );
};

export default TermsOfUse;