import React from 'react'
import { motion } from 'framer-motion'

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-1.5">
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          className="w-2 h-2 bg-primary/60 rounded-full"
          animate={{ y: [-4, 4, -4] }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: index * 0.1,
          }}
        />
      ))}
    </div>
  )
}
