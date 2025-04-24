// src/components/AuthButtons.tsx
import { useSession, signIn, signOut } from 'next-auth/react';

const AuthButtons: React.FC = () => {
  const { data: session } = useSession();

  return (
    <div>
      {session ? (
        <button
          onClick={() => signOut()}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
        >
          Sign Out
        </button>
      ) : (
        <button
          onClick={() => signIn()}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Sign In
        </button>
      )}
    </div>
  );
};

export default AuthButtons;