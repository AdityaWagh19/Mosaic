import { useState, useEffect } from 'react';
import type { RefObject } from 'react';

export const useResizeObserver = <T extends HTMLElement>(ref: RefObject<T | null>) => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!ref.current) return;

    const observer = new ResizeObserver(entries => {
      if (entries.length === 0) return;
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });

    observer.observe(ref.current);
    
    // Initial dimensions
    setDimensions({ 
      width: ref.current.clientWidth, 
      height: ref.current.clientHeight 
    });

    return () => observer.disconnect();
  }, [ref]);

  return dimensions;
};
