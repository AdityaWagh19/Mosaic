import * as Tooltip from '@radix-ui/react-tooltip';
import { CircleHelp } from 'lucide-react';
export function InfoTooltip({ label }: { label: string }) { return <Tooltip.Provider delayDuration={180}><Tooltip.Root><Tooltip.Trigger className="tooltip-trigger" aria-label={label}><CircleHelp size={14} strokeWidth={1.8} /></Tooltip.Trigger><Tooltip.Portal><Tooltip.Content className="tooltip-content" sideOffset={6}>{label}<Tooltip.Arrow className="tooltip-arrow" /></Tooltip.Content></Tooltip.Portal></Tooltip.Root></Tooltip.Provider>; }
