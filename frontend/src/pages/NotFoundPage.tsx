import { Link } from 'react-router-dom'

import { buttonClasses } from '../components/Button'

export function NotFoundPage() {
  return (
    <div className="mx-auto max-w-md py-16 text-center">
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="mt-2 text-sm text-slate-400">
        That address does not match anything in the study app.
      </p>
      <Link to="/" className={`${buttonClasses('primary')} mt-6`}>
        Back to dashboard
      </Link>
    </div>
  )
}
