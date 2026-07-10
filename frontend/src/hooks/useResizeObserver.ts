import { useState, useEffect, RefObject } from 'react';

export const useResizeObserver = (ref: RefObject<HTMLElement>) => {
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
