import * as Toast from '@radix-ui/react-toast';
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

type ToastContextValue = { notify: (message: string) => void };
const ToastContext = createContext<ToastContextValue | undefined>(undefined);
export function MosaicToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState(''); const [open, setOpen] = useState(false);
  const value = useMemo(() => ({ notify: (next: string) => { setMessage(next); setOpen(true); } }), []);
  return <ToastContext.Provider value={value}><Toast.Provider swipeDirection="right">{children}<Toast.Root className="toast" open={open} onOpenChange={setOpen} duration={2600}><Toast.Description>{message}</Toast.Description></Toast.Root><Toast.Viewport className="toast-viewport" /></Toast.Provider></ToastContext.Provider>;
}
// eslint-disable-next-line react-refresh/only-export-components
export function useToast() { return useContext(ToastContext) ?? { notify: () => undefined }; }
