import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'

type Props = {
  icons: LucideIcon[]
  messages: string[]
  title?: string
}

export default function LoadingScene({ icons, messages, title }: Props) {
  const [i, setI] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % messages.length), 1900)
    return () => clearInterval(t)
  }, [messages.length])

  const Icon = icons[i % icons.length]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-16 flex flex-col items-center justify-center gap-6 text-center overflow-hidden relative"
    >
      {title && <h2 className="relative text-lg font-display font-semibold text-slate-200">{title}</h2>}

      <div className="relative w-28 h-28 flex items-center justify-center">
        <motion.span
          className="absolute inset-0 rounded-full bg-amber-400/10 blur-2xl"
          animate={{ scale: [1, 1.35, 1] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.span
          className="absolute inset-1 rounded-full border-2 border-dashed border-white/15"
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
        />
        <motion.span
          className="absolute inset-4 rounded-full border-t-2 border-white/50"
          animate={{ rotate: -360 }}
          transition={{ duration: 2.6, repeat: Infinity, ease: 'linear' }}
        />
        <AnimatePresence mode="wait">
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.4, rotate: -25 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            exit={{ opacity: 0, scale: 0.4, rotate: 25 }}
            transition={{ duration: 0.35, ease: 'backOut' }}
            className="relative w-14 h-14 rounded-md border border-amber-300/30 bg-amber-400/10 flex items-center justify-center"
          >
            <Icon className="w-7 h-7 text-amber-300" />
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="h-6 relative w-full max-w-sm mx-auto">
        <AnimatePresence mode="wait">
          <motion.p
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 text-sm text-slate-300 font-medium"
          >
            {messages[i]}
          </motion.p>
        </AnimatePresence>
      </div>

      <div className="relative w-56 h-1.5 rounded-full bg-white/10 overflow-hidden">
        <motion.div
          className="h-full w-1/3 rounded-full bg-amber-400/80 motion-reduce:hidden"
          animate={{ x: ['-100%', '250%'] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
    </motion.div>
  )
}
