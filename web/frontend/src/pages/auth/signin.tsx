import { GetServerSidePropsContext } from 'next';
import { signIn, getCsrfToken } from 'next-auth/react';
import { useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/common/Layout';
import { LogIn, User, Lock } from 'lucide-react';

export default function SignIn({ csrfToken }: { csrfToken: string }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await signIn('credentials', {
      username,
      password,
      redirect: false,
    });

    if (result?.error) {
      setError('Invalid credentials. Please try again.');
    } else {
      router.push('/');
    }
    
    setIsLoading(false);
  };

  return (
    <Layout>
      <div className="min-h-screen flex items-center justify-center py-12">
        <div className="max-w-md w-full">
          <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 backdrop-blur-sm rounded-xl p-8 shadow-2xl border border-blue-400/20">
            <div className="text-center mb-8">
              <div className="bg-white/20 backdrop-blur-sm p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center border border-white/30">
                <LogIn className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">Sign In</h1>
              <p className="text-blue-100">Access the Berlin Transport Project</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <input name="csrfToken" type="hidden" defaultValue={csrfToken} />
              
              <div>
                <label className="block text-sm font-medium text-blue-100 mb-2">
                  <User className="inline h-4 w-4 mr-2" />
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg text-white placeholder-blue-200 focus:ring-2 focus:ring-blue-300 focus:border-transparent transition-all"
                  placeholder="Enter your username"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-blue-100 mb-2">
                  <Lock className="inline h-4 w-4 mr-2" />
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg text-white placeholder-blue-200 focus:ring-2 focus:ring-blue-300 focus:border-transparent transition-all"
                  placeholder="Enter your password"
                  required
                />
              </div>

              {error && (
                <div className="bg-red-500/20 border border-red-400/30 text-red-100 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-white text-blue-600 px-4 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-1 hover:shadow-lg"
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-blue-200">
              This area is for project administrators only.
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export async function getServerSideProps(context: GetServerSidePropsContext) {
  return {
    props: {
      csrfToken: await getCsrfToken(context),
    },
  };
}