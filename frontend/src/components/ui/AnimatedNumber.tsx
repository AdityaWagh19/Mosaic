import { animate, useReducedMotion } from 'motion/react';
import { useEffect, useState } from 'react';

export function AnimatedNumber({ value, format }: { value: number; format: (value: number) => string }) {
  const reduced = useReducedMotion(); const [shown, setShown] = useState(reduced ? value : 0);
  useEffect(() => { if (reduced) { setShown(value); return; } const controls = animate(0, value, { duration: .45, ease: 'easeOut', onUpdate: setShown }); return () => controls.stop(); }, [value, reduced]);
  return <>{format(shown)}</>;
}
