import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import CredentialsProvider from 'next-auth/providers/credentials'

export default NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        // Simple demo authentication
        if (credentials.email === 'demo@example.com' && credentials.password === 'password') {
          return {
            id: 'demo_user',
            email: 'demo@example.com',
            name: 'Demo User'
          }
        }
        return null
      }
    })
  ],
  callbacks: {
    async jwt({ token, account, user }) {
      if (account) {
        token.accessToken = account.access_token
      } else if (user) {
        // For credentials provider, use a demo token
        token.accessToken = 'demo_token'
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken || 'demo_token'
      return session
    },
  },
  pages: {
    signIn: '/auth/signin',
  },
  secret: process.env.NEXTAUTH_SECRET,
})