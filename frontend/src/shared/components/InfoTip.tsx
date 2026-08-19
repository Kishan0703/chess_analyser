import type { ReactNode } from 'react'

// Small hover tooltip. Usage: <InfoTip>explanatory text</InfoTip> renders an
// ⓘ affordance; <InfoTip label="Run engine">text</InfoTip> wraps custom content.
interface InfoTipProps {
  children: ReactNode
  label?: ReactNode
  side?: string
}

export default function InfoTip({ children, label, side = 'top' }: InfoTipProps) {
  return (
    <span className={`infotip infotip-${side}`} tabIndex={0}>
      {label ?? <span className="infotip-dot">i</span>}
      <span className="infotip-bubble" role="tooltip">{children}</span>
    </span>
  )
}
