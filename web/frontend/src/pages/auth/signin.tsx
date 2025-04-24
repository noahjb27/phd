import { GetServerSidePropsContext } from 'next';
import { signIn, getCsrfToken } from 'next-auth/react';
import { useState } from 'react';
import { useRouter } from 'next/router';

export default function SignIn({ csrfToken }: { csrfToken: string }) {
  const [username, setUsername] = useState(''); // Hooks inside the component
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await signIn('credentials', {
      username,
      password,
      redirect: false, // Avoid redirecting, we will handle navigation
    });

    if (result?.error) {
      setError('Invalid credentials');
    } else {
      router.push('/'); // Redirect to the home page or any protected page
    }
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded shadow-md">
        <input name="csrfToken" type="hidden" defaultValue={csrfToken} />
        <div>
          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="border p-2 rounded w-full"
            />
          </label>
        </div>
        <div>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border p-2 rounded w-full"
            />
          </label>
        </div>
        {error && <div className="text-red-500">{error}</div>}
        <button type="submit" className="btn btn-primary mt-4">
          Sign In
        </button>
      </form>
    </div>
  );
}

export async function getServerSideProps(context: GetServerSidePropsContext) {
  return {
    props: {
      csrfToken: await getCsrfToken(context), // Fetch CSRF token for form submission
    },
  };
}
