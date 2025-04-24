// pages/citations.tsx
import Layout from '@/components/common/Layout';

const Citations = () => {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8">Citations and References</h1>
        
        <div className="prose prose-gray max-w-none">
          <section className="mb-8">
            <h2>How to Cite This Project</h2>
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="font-mono text-sm">
                Baumann, N. (2025). Berlin Public Transport History: A Digital History of Berlin's Cold War Public Transportation. https://berlin-transport-history.me
              </p>
            </div>
            
            <h3 className="mt-6">BibTeX</h3>
            <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
              {`@misc{berlinTransport2024,
  author = {Baumann, Noah},
  title = {Berlin Public Transport History: A Digital History of Berlin's Cold War Public Transportation},
  year = {2025},
  publisher = {Humboldt University of Berlin},
  url = {https://berlin-transport-history.me}
}`}
            </pre>
          </section>

          <section className="mb-8">
            <h2>Data Sources</h2>
            <ul>
              <li>
                <strong>Historical Maps:</strong> Berliner Landesarchiv & Staatsbibliothek Berlin
              </li>
              <li>
                <strong>Transportation Records:</strong> BVG Archives
              </li>
              <li>
                <strong>Statistical Data:</strong> Statistische Jahrbücher Berlin
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2>Key References</h2>
            <ul>
              <li>
                <p>
                  <strong>Primary Sources:</strong> List key archival sources, historical documents, and primary materials
                </p>
              </li>
              <li>
                <p>
                  <strong>Secondary Literature:</strong> List important academic works that informed the project
                </p>
              </li>
              <li>
                <p>
                  <strong>Digital Resources:</strong> List digital archives and tools used
                </p>
              </li>
            </ul>
          </section>

          <p className="text-sm text-gray-500 mt-8">Last updated: January 2025</p>
        </div>
      </div>
    </Layout>
  );
};

export default Citations;