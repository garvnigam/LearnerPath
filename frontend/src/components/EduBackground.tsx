import {
  BookOpen, GraduationCap, Atom, Lightbulb, PenTool, Calculator,
  FlaskConical, Code2, Globe2, Sigma, Brain, Microscope,
} from 'lucide-react'

const PARTICLES = [
  { Icon: GraduationCap, top: '8%', left: '6%', size: 34, duration: 17, delay: 0, dx: '30px', rot: '12deg', opacity: 0.16 },
  { Icon: BookOpen, top: '16%', left: '85%', size: 30, duration: 19, delay: 1.2, dx: '-24px', rot: '-10deg', opacity: 0.14 },
  { Icon: Atom, top: '62%', left: '92%', size: 32, duration: 21, delay: 2.4, dx: '-20px', rot: '20deg', opacity: 0.15 },
  { Icon: Lightbulb, top: '78%', left: '10%', size: 28, duration: 15, delay: 0.6, dx: '18px', rot: '-14deg', opacity: 0.15 },
  { Icon: PenTool, top: '38%', left: '3%', size: 24, duration: 18, delay: 3, dx: '26px', rot: '16deg', opacity: 0.13 },
  { Icon: Calculator, top: '4%', left: '45%', size: 26, duration: 20, delay: 1.8, dx: '-16px', rot: '8deg', opacity: 0.13 },
  { Icon: FlaskConical, top: '55%', left: '48%', size: 30, duration: 22, delay: 4, dx: '22px', rot: '-12deg', opacity: 0.12 },
  { Icon: Code2, top: '88%', left: '70%', size: 30, duration: 16, delay: 2.2, dx: '-28px', rot: '10deg', opacity: 0.15 },
  { Icon: Globe2, top: '28%', left: '68%', size: 32, duration: 23, delay: 0.9, dx: '20px', rot: '-18deg', opacity: 0.14 },
  { Icon: Sigma, top: '70%', left: '30%', size: 24, duration: 14, delay: 3.6, dx: '-18px', rot: '14deg', opacity: 0.13 },
  { Icon: Brain, top: '92%', left: '42%', size: 28, duration: 19, delay: 1.5, dx: '24px', rot: '-8deg', opacity: 0.14 },
  { Icon: Microscope, top: '46%', left: '18%', size: 26, duration: 17, delay: 4.4, dx: '-22px', rot: '12deg', opacity: 0.12 },
]

export default function EduBackground() {
  return (
    <div className="fixed inset-0 -z-30 overflow-hidden pointer-events-none">
      {PARTICLES.map((p, i) => {
        const Icon = p.Icon
        return (
          <div
            key={i}
            className="absolute animate-edu-drift motion-reduce:hidden text-white"
            style={{
              top: p.top,
              left: p.left,
              opacity: p.opacity,
              animationDuration: `${p.duration}s`,
              animationDelay: `${p.delay}s`,
              // @ts-ignore custom properties consumed by the keyframe
              '--edu-dx': p.dx,
              '--edu-rot': p.rot,
            }}
          >
            <Icon size={p.size} strokeWidth={1.5} />
          </div>
        )
      })}
    </div>
  )
}
