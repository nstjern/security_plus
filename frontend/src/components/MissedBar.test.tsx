import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MissedBar } from './MissedBar'

describe('MissedBar', () => {
  it('scales the bar against the largest miss count in the list', () => {
    const { container } = render(
      <div className="w-40">
        <MissedBar missed={2} maxMissed={4} />
      </div>,
    )

    const fill = container.querySelector('.bg-rose-500')
    expect(fill).toHaveStyle({ width: '50%' })
  })
})
