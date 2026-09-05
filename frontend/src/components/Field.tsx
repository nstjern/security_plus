import { useId } from 'react'
import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'

const CONTROL_CLASSES =
  'w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 disabled:opacity-50'

interface FieldShellProps {
  label: string
  hint?: string
  id: string
  children: ReactNode
}

function FieldShell({ label, hint, id, children }: FieldShellProps) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-slate-200">
        {label}
      </label>
      {children}
      {hint ? (
        <p id={`${id}-hint`} className="text-xs text-slate-400">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  hint?: string
}

export function TextField({ label, hint, ...props }: TextFieldProps) {
  const generatedId = useId()
  const id = props.id ?? generatedId
  return (
    <FieldShell label={label} hint={hint} id={id}>
      <input
        id={id}
        className={CONTROL_CLASSES}
        aria-describedby={hint ? `${id}-hint` : undefined}
        {...props}
      />
    </FieldShell>
  )
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string
  hint?: string
  children: ReactNode
}

export function SelectField({ label, hint, children, ...props }: SelectFieldProps) {
  const generatedId = useId()
  const id = props.id ?? generatedId
  return (
    <FieldShell label={label} hint={hint} id={id}>
      <select
        id={id}
        className={CONTROL_CLASSES}
        aria-describedby={hint ? `${id}-hint` : undefined}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  )
}
