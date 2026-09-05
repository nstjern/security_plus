import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'

import { App } from '../App'

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      // Retries turn a deliberate failure fixture into a slow test for no benefit.
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

interface ProvidersProps {
  children: ReactNode
  route: string
  queryClient: QueryClient
}

function Providers({ children, route, queryClient }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

/** Renders the whole application, so routing and the auth guard are exercised too. */
export function renderApp(route = '/') {
  // Built once per render rather than inside the wrapper component, which would hand the
  // tree a brand new cache on every re-render.
  const queryClient = createTestQueryClient()

  return {
    user: userEvent.setup(),
    queryClient,
    ...render(<App />, {
      wrapper: ({ children }) => (
        <Providers route={route} queryClient={queryClient}>
          {children}
        </Providers>
      ),
    }),
  }
}
