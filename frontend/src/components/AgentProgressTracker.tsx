import React from 'react';
import { CheckCircle, Loader2, Circle, ShieldCheck } from 'lucide-react';

interface Step {
  id: string;
  name: string;
  desc: string;
  status: 'pending' | 'running' | 'completed';
}

interface AgentProgressTrackerProps {
  currentStepIndex: number;
}

export const AGENT_STEPS = [
  { id: '1', name: 'Claim Extraction Agent', desc: 'Parsing atomic claims & entities' },
  { id: '2', name: 'Web Research Agent', desc: 'Searching primary sources & official web data' },
  { id: '3', name: 'Evidence Verification Agent', desc: 'Comparing claims vs supporting & contradicting data' },
  { id: '4', name: 'Source Credibility Agent', desc: 'Evaluating domain authority & publisher metrics' },
  { id: '5', name: 'Bias & Manipulation Agent', desc: 'Analyzing sensationalism & clickbait framing' },
  { id: '6', name: 'Cross-Source Consistency Agent', desc: 'Corroborating independent publisher agreement' },
  { id: '7', name: 'Final Judge Agent', desc: 'Synthesizing transparent verdict & confidence' }
];

export const AgentProgressTracker: React.FC<AgentProgressTrackerProps> = ({ currentStepIndex }) => {
  return (
    <div className="w-full max-w-2xl mx-auto glass-panel rounded-2xl p-6 border border-slate-800 shadow-2xl space-y-4">
      <div className="flex items-center space-x-3 pb-3 border-b border-slate-800">
        <ShieldCheck className="w-6 h-6 text-cyan-400 animate-pulse" />
        <div>
          <h3 className="text-lg font-bold text-white">Multi-Agent AI Investigation Engine</h3>
          <p className="text-xs text-slate-400">Real-time coordinated agent execution graph</p>
        </div>
      </div>

      <div className="space-y-3">
        {AGENT_STEPS.map((step, idx) => {
          let state: 'pending' | 'running' | 'completed' = 'pending';
          if (idx < currentStepIndex) state = 'completed';
          else if (idx === currentStepIndex) state = 'running';

          return (
            <div 
              key={step.id}
              className={`flex items-center justify-between p-3 rounded-xl transition-all duration-300 ${
                state === 'running' 
                  ? 'bg-cyan-950/40 border border-cyan-500/40 shadow-lg shadow-cyan-950/20' 
                  : state === 'completed'
                  ? 'bg-slate-900/60 border border-slate-800/80 text-slate-300'
                  : 'bg-slate-900/20 border border-slate-800/30 text-slate-500 opacity-60'
              }`}
            >
              <div className="flex items-center space-x-3">
                {state === 'completed' && <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />}
                {state === 'running' && <Loader2 className="w-5 h-5 text-cyan-400 animate-spin shrink-0" />}
                {state === 'pending' && <Circle className="w-5 h-5 text-slate-600 shrink-0" />}

                <div>
                  <div className={`font-semibold text-sm ${state === 'running' ? 'text-cyan-300' : state === 'completed' ? 'text-slate-200' : 'text-slate-500'}`}>
                    {step.name}
                  </div>
                  <div className="text-xs text-slate-400">{step.desc}</div>
                </div>
              </div>

              <div className="text-xs font-mono">
                {state === 'completed' && <span className="text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800/50">Done</span>}
                {state === 'running' && <span className="text-cyan-300 bg-cyan-950/50 px-2 py-0.5 rounded border border-cyan-800/50 animate-pulse">Processing...</span>}
                {state === 'pending' && <span className="text-slate-600">Waiting</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
