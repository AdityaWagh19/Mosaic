import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { MosaicToastProvider } from './components/ui/ToastProvider.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MosaicToastProvider><App /></MosaicToastProvider>
  </StrictMode>,
)
