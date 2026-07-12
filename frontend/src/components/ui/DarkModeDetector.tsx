import { useEffect } from 'react';
import { useToast } from './ToastProvider';

export function DarkModeDetector() {
  const { notify } = useToast();

  useEffect(() => {
    const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (isDark) {
      notify('Mosaic is designed as a bright-white UI. Dark mode is not supported.');
    }
  }, [notify]);

  return null;
}
