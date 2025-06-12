import Layout from '../components/common/Layout';

const Impressum: React.FC = () => (
  <Layout>
    <section className="max-w-4xl mx-auto px-6 py-12">
      {/* Header with gradient background */}
      <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20 mb-8">
        <h1 className="text-4xl font-bold text-white mb-4">Impressum</h1>
        <p className="text-lg text-blue-100">
          This website is maintained in accordance with German law. Below, you will find the required legal information.
        </p>
      </div>

      {/* Content with semi-transparent background */}
      <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 shadow-2xl border border-white/20">
        <div className="space-y-6 text-gray-200">
          <div>
            <h2 className="text-2xl font-semibold text-white mb-4">Responsible for Content</h2>
            <p className="leading-relaxed">
              Noah Jefferson Baumann <br />
              Friedrichstrasse 191, <br />
              10117 Berlin <br />
              Germany
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-white mb-4">Contact Information</h2>
            <p className="leading-relaxed">
              Email: <a href="mailto:noah.baumann@yahoo.de" className="text-blue-300 hover:text-blue-200 transition-colors">noah.baumann@yahoo.de</a>
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-white mb-4">Disclaimer</h2>
            <p className="leading-relaxed">
              While every effort is made to ensure the accuracy of the information on this website, I cannot accept responsibility for any errors or omissions. External links are provided for informational purposes only, and I am not responsible for the content of external websites.
            </p>
          </div>
        </div>
      </div>
    </section>
  </Layout>
);

export default Impressum;
