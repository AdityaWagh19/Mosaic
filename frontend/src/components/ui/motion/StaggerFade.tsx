import { motion, useReducedMotion } from 'motion/react';
import type { ReactNode } from 'react';

export function StaggerFade({ children, stagger = 0.06 }: { children: ReactNode[]; stagger?: number }) {
  const reduced = useReducedMotion();
  const variants = {
    hidden: { opacity: reduced ? 1 : 0, y: reduced ? 0 : 4 },
    visible: { opacity: 1, y: 0 }
  };
  return (
    <>
      {children.map((child, i) => (
        <motion.div
          key={i}
          initial="hidden"
          animate="visible"
          variants={variants}
          transition={{ delay: i * stagger, duration: 0.2, ease: 'easeOut' }}
          style={{ width: '100%', height: '100%', display: 'flex' }}
        >
          {child}
        </motion.div>
      ))}
    </>
  );
}
