import Layout from '../components/common/Layout';

const Impressum: React.FC = () => (
  <Layout>
    <section className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="text-4xl font-bold text-primary mb-6">Impressum</h1>
      <p className="text-lg text-gray-700 mb-4">
        This website is maintained in accordance with German law. Below, you will find the required legal information.
      </p>

      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-primary">Responsible for Content</h2>
          <p className="text-gray-700 mt-2">
            Noah Jefferson Baumann <br />
            Pritzwalker Strasse 16, <br />
            10559 Berlin <br />
            Germany
          </p>
        </div>

        <div>
          <h2 className="text-2xl font-semibold text-primary">Contact Information</h2>
          <p className="text-gray-700 mt-2">
            Email: noah.baumann@yahoo.de <br />
          </p>
        </div>

        <div>
          <h2 className="text-2xl font-semibold text-primary">Disclaimer</h2>
          <p className="text-gray-700 mt-2">
            While every effort is made to ensure the accuracy of the information on this website, I cannot accept responsibility for any errors or omissions. External links are provided for informational purposes only, and I am not responsible for the content of external websites.
          </p>
        </div>
      </div>
    </section>
  </Layout>
);

export default Impressum;
