import React from 'react';
import { VerdictType } from '../types';
import { CheckCircle2, XCircle, AlertTriangle, HelpCircle, AlertCircle, Scale } from 'lucide-react';

interface VerdictBadgeProps {
  verdict: VerdictType;
  size?: 'sm' | 'md' | 'lg';
}

export const VerdictBadge: React.FC<VerdictBadgeProps> = ({ verdict, size = 'md' }) => {
  const getBadgeStyle = () => {
    switch (verdict) {
      case 'VERIFIED':
        return {
          bg: 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300',
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        };
      case 'FALSE':
        return {
          bg: 'bg-rose-950/80 border-rose-500/50 text-rose-300',
          icon: <XCircle className="w-4 h-4 text-rose-400" />
        };
      case 'MISLEADING':
        return {
          bg: 'bg-amber-950/80 border-amber-500/50 text-amber-300',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />
        };
      case 'PARTIALLY TRUE':
        return {
          bg: 'bg-yellow-950/80 border-yellow-500/50 text-yellow-300',
          icon: <Scale className="w-4 h-4 text-yellow-400" />
        };
      case 'UNVERIFIED':
        return {
          bg: 'bg-sky-950/80 border-sky-500/50 text-sky-300',
          icon: <HelpCircle className="w-4 h-4 text-sky-400" />
        };
      case 'UNCERTAIN':
      case 'INSUFFICIENT EVIDENCE':
      default:
        return {
          bg: 'bg-slate-800/90 border-slate-600/50 text-slate-300',
          icon: <AlertCircle className="w-4 h-4 text-slate-400" />
        };
    }
  };

  const style = getBadgeStyle();
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 space-x-1',
    md: 'text-sm px-3 py-1 space-x-1.5 font-semibold',
    lg: 'text-base px-4 py-1.5 space-x-2 font-bold tracking-wide'
  }[size];

  return (
    <span className={`inline-flex items-center rounded-full border shadow-sm ${style.bg} ${sizeClasses}`}>
      {style.icon}
      <span>{verdict}</span>
    </span>
  );
};
