import React, { useEffect, useState } from 'react';
import { getDemoClaims, verifyText } from '../services/api';
import { DemoClaimItem, FactCheckResponse } from '../types';
import { AgentProgressTracker, AGENT_STEPS } from '../components/AgentProgressTracker';
import { ResultsDashboardPage } from './ResultsDashboardPage';
import { Layers, Play, Loader2, ShieldCheck, ArrowLeft } from 'lucide-react';

export const DemoModePage: React.FC = () => {
  const [demoClaims, setDemoClaims] = useState<DemoClaimItem[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  
  const [activeClaim, setActiveClaim] = useState<DemoClaimItem | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [result, setResult] = useState<FactCheckResponse | null>(null);

  useEffect(() => {
    getDemoClaims()
      .then(setDemoClaims)
      .catch(console.error)
      .finally(() => setIsLoadingList(false));
  }, []);

  const handleRunDemo = async (claim: DemoClaimItem) => {
    setActiveClaim(claim);
    setIsProcessing(true);
    setCurrentStep(0);
    setResult(null);

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < AGENT_STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 700);

    try {
      const res = await verifyText(claim.input_text);
      clearInterval(stepInterval);
      setCurrentStep(AGENT_STEPS.length);
      setResult(res);
    } catch (e: any) {
      clearInterval(stepInterval);
      alert('Demo execution error: ' + (e.message || 'Pipeline failure'));
    } finally {
      setIsProcessing(false);
    }
  };

  if (result) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => { setResult(null); setActiveClaim(null); }}
          className="inline-flex items-center space-x-2 text-sm text-cyan-400 hover:text-cyan-300 font-medium glass-panel px-4 py-2 rounded-xl border border-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Select Another Demo Claim</span>
        </button>
        <ResultsDashboardPage data={result} />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 py-6 px-4">
      
      <div className="text-center space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-cyan-300 text-xs font-semibold">
          <Layers className="w-3.5 h-3.5" />
          <span>Faculty & Academic Evaluation Mode</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">Controlled Faculty Demo Mode</h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          Select any of the 10 pre-configured academic test scenarios below to execute the real multi-agent pipeline live.
        </p>
      </div>

      {isProcessing && (
        <div className="space-y-4">
          <div className="text-center text-sm text-cyan-300 font-semibold">
            Running Demo Scenario: "{activeClaim?.title}"
          </div>
          <AgentProgressTracker currentStepIndex={currentStep} />
        </div>
      )}

      {!isProcessing && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {demoClaims.map((item) => (
            <div
              key={item.id}
              className="glass-panel p-6 rounded-2xl border border-slate-800 hover:border-cyan-500/40 space-y-4 flex flex-col justify-between transition-all group"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                    {item.category}
                  </span>
                  <span className="text-xs font-semibold text-slate-400">
                    Expected: {item.expected_verdict}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                  {item.title}
                </h3>

                <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800 font-mono">
                  "{item.input_text}"
                </p>

                <p className="text-xs text-slate-400">
                  {item.description}
                </p>
              </div>

              <button
                onClick={() => handleRunDemo(item)}
                className="w-full bg-slate-800 hover:bg-cyan-900 text-cyan-300 border border-slate-700 font-semibold text-xs py-2.5 rounded-xl flex items-center justify-center space-x-2 transition-all shadow-sm"
              >
                <Play className="w-3.5 h-3.5 fill-cyan-300" />
                <span>Execute Agent Pipeline</span>
              </button>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};
