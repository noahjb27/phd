import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import jwt from 'jsonwebtoken';

export default NextAuth({
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: 'Username', type: 'text' },
        password: { label: 'Password', type: 'password' },
      },
      authorize: async (credentials) => {
        if (credentials?.username === 'admin' && credentials?.password === '2710') {
          return { id: '1', name: 'Admin User', role: 'admin' }; // Example user object
        }
        return null;
      },
    }),
  ],
  pages: {
    signIn: '/auth/signin',
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = (user as any).id;
        token.role = (user as any).role;
      }
      return token; 
    },
    async session({ session, token }) {
      session.user.id = token.id as string | undefined;
      session.user.role = token.role as string | undefined;
      if (!process.env.JWT_SECRET) {
        throw new Error('JWT_SECRET is not defined');
      }
      session.accessToken = jwt.sign(
        { id: token.id, role: token.role },
        process.env.JWT_SECRET, // Ensure this is set
        { expiresIn: '1h' }
      );
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET, // Ensure this is set
});
