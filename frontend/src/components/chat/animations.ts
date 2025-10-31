import { Variants } from 'framer-motion'

export const messageVariants: Variants = {
  initial: {
    opacity: 0,
    y: 10,
    scale: 0.95,
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.3,
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    scale: 0.95,
    transition: {
      duration: 0.2,
    },
  },
}

export const bubbleVariants: Variants = {
  initial: { width: 0 },
  animate: {
    width: '100%',
    transition: {
      duration: 0.4,
    },
  },
}

export const typingIndicatorVariants: Variants = {
  animate: {
    opacity: [0.3, 1, 0.3],
    transition: {
      duration: 1.5,
      repeat: Infinity,
    },
  },
}

export const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
}
