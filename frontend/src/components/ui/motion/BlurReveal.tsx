import { motion, useReducedMotion } from 'motion/react';
import { type ReactNode, type HTMLAttributes } from 'react';

const motionComponents = {
  h1: motion.h1,
  h2: motion.h2,
  div: motion.div,
  p: motion.p,
  span: motion.span
};

export function BlurReveal({ children, as = 'div', className = '', ...rest }: { children: ReactNode; as?: keyof typeof motionComponents; className?: string } & HTMLAttributes<HTMLElement>) {
  const reduced = useReducedMotion();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Component = (motionComponents[as as keyof typeof motionComponents] || motion.div) as any;

  return (
    <Component
      initial={{ opacity: reduced ? 1 : 0, filter: reduced ? 'blur(0px)' : 'blur(4px)', y: reduced ? 0 : 4 }}
      whileInView={{ opacity: 1, filter: 'blur(0px)', y: 0 }}
      viewport={{ once: true, margin: '-20px' }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={className}
      {...rest}
    >
      {children}
    </Component>
  );
}
