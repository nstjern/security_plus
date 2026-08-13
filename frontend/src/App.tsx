import { Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthProvider'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { BrowsePage } from './pages/BrowsePage'
import { DashboardPage } from './pages/DashboardPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ReviewGuidePage } from './pages/ReviewGuidePage'
import { SessionPage } from './pages/SessionPage'
import { SessionSummaryPage } from './pages/SessionSummaryPage'
import { SignInPage } from './pages/SignInPage'
import { StartSessionPage } from './pages/StartSessionPage'

/** Everything except sign-in requires a session; the guard redirects and remembers where. */
const PROTECTED_ROUTES = [
  { path: '/', element: <DashboardPage /> },
  { path: '/study', element: <StartSessionPage /> },
  { path: '/sessions/:sessionId', element: <SessionPage /> },
  { path: '/sessions/:sessionId/summary', element: <SessionSummaryPage /> },
  { path: '/review-guide', element: <ReviewGuidePage /> },
  { path: '/questions', element: <BrowsePage /> },
]

export function App() {
  return (
    <AuthProvider>
      <Layout>
        <Routes>
          <Route path="/sign-in" element={<SignInPage />} />
          {PROTECTED_ROUTES.map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={<RequireAuth>{route.element}</RequireAuth>}
            />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Layout>
    </AuthProvider>
  )
}
