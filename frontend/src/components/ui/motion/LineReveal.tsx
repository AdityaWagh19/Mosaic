import { motion, useReducedMotion, type HTMLMotionProps } from 'motion/react';

export function LineReveal({ className = '', style, ...rest }: { className?: string } & Omit<HTMLMotionProps<"hr">, "ref">) {
  const reduced = useReducedMotion();

  return (
    <motion.hr
      className={className}
      initial={{ scaleX: reduced ? 1 : 0 }}
      whileInView={{ scaleX: 1 }}
      viewport={{ once: true, margin: '-20px' }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      style={{ originX: 0, ...style }}
      {...rest}
    />
  );
}
