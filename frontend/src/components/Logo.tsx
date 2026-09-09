interface LogoProps {
  compact?: boolean
}

export function Logo({compact = false}: LogoProps) {
  return (
    <div className="logo-lockup" aria-label="Reservoir home">
      <span className="logo-mark" aria-hidden="true">
        <span className="logo-wave" />
      </span>
      {!compact && <span className="logo-word">Reservoir</span>}
    </div>
  )
}
