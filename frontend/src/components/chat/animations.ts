import { motion } from 'framer-motion'

export const messageVariants = {
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
      ease: 'easeOut',
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    scale: 0.95,
    transition: {
      duration: 0.2,
      ease: 'easeIn',
    },
  },
}

export const bubbleVariants = {
  initial: { width: 0 },
  animate: {
    width: '100%',
    transition: {
      duration: 0.4,
      ease: 'easeOut',
    },
  },
}

export const typingIndicatorVariants = {
  animate: {
    opacity: [0.3, 1, 0.3],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
}

export const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
}
