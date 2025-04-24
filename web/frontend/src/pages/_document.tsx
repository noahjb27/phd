// src/pages/_document.tsx
import Document, { Html, Head, Main, NextScript, DocumentContext } from 'next/document';

class MyDocument extends Document {
  static async getInitialProps(ctx: DocumentContext) {
    const initialProps = await Document.getInitialProps(ctx);
    return { ...initialProps };
  }

  render() {
    return (
      <Html lang="en">
        <Head>
          <link rel="icon" href="/favicon_io/favicon.ico" />
          <link rel="apple-touch-icon" sizes="180x180" href="/favicon_io/apple-touch-icon.png" />
          <link rel="icon" type="image/png" sizes="32x32" href="/favicon_io/favicon-32x32.png" />
          <link rel="icon" type="image/png" sizes="16x16" href="/favicon_io/favicon-16x16.png" />
        </Head>
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}

export default MyDocument;
