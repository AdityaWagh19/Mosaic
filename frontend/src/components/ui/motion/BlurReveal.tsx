import { motion, useReducedMotion } from 'motion/react';
import React, { type ReactNode, type HTMLAttributes } from 'react';

export function BlurReveal({ children, as = 'div', className = '', ...rest }: { children: ReactNode; as?: keyof typeof motion; className?: string } & HTMLAttributes<HTMLElement>) {
  const reduced = useReducedMotion();
  const Component = motion[as as keyof typeof motion] as React.ElementType;

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
