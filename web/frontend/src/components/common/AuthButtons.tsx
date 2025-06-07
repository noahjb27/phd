import { useSession, signIn, signOut } from 'next-auth/react';

const AuthButtons: React.FC = () => {
  const { data: session } = useSession();

  return (
    <div>
      {session ? (
        <button
          onClick={() => signOut()}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600/80 hover:bg-red-600 rounded-md transition-all duration-200 hover:shadow-lg transform hover:-translate-y-0.5 backdrop-blur-sm border border-red-500/30"
        >
          Sign Out
        </button>
      ) : (
        <button
          onClick={() => signIn()}
          className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600/80 to-purple-600/80 hover:from-blue-600 hover:to-purple-600 rounded-md transition-all duration-200 hover:shadow-lg transform hover:-translate-y-0.5 backdrop-blur-sm border border-blue-500/30"
        >
          Sign In
        </button>
      )}
    </div>
  );
};

export default AuthButtons;