import NextAuth, { DefaultSession, DefaultUser } from 'next-auth';

declare module 'next-auth' {
  interface Session {
    user: {
      id?: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      role?: string; // Add the role property to the user in the session
    } & DefaultSession['user'];
    accessToken?: string; // Add the accessToken property to the session
  }

  interface User extends DefaultUser {
    id: string;
    role?: string; // Add the role property to the User type
  }

  interface JWT {
    id?: string;
    role?: string;
  }
}
