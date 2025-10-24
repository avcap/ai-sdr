import { SessionProvider } from 'next-auth/react'
import { Toaster } from 'react-hot-toast'
import '../styles/globals.css'

export default function App({
  Component,
  pageProps: { session, ...pageProps },
}) {
  return (
    <SessionProvider session={session}>
      <Component {...pageProps} />
      <Toaster position="top-right" />
    </SessionProvider>
  )
}
