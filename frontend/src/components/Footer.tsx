import React from 'react';
import { ShieldCheck, Info, Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="glass-panel border-t border-slate-800/80 mt-20 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-1.5 bg-cyan-950 text-cyan-400 rounded-lg border border-cyan-800">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="font-bold text-white text-lg">FactGuard AI</span>
            <span className="text-xs text-slate-400">| Multi-Agent Social Media Fact-Checking Platform</span>
          </div>

          <div className="text-xs text-slate-400 text-center md:text-right">
            B.Tech Final-Year Project Demonstration Platform
          </div>
        </div>

        {/* Academic Mandatory Disclaimer */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3 text-xs text-slate-400">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <p>
            <strong>Academic Disclaimer:</strong> FactGuard AI provides evidence-based automated analysis using multi-agent AI and web retrieval. It is designed to assist evaluation and is not a substitute for authoritative human journalism or professional advice.
          </p>
        </div>

        <div className="pt-4 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <div>© 2026 FactGuard AI Platform. All rights reserved.</div>
          <div className="mt-2 sm:mt-0 flex items-center space-x-1">
            <span>Built with</span>
            <Heart className="w-3 h-3 text-rose-500 fill-rose-500" />
            <span>FastAPI, LangGraph & React</span>
          </div>
        </div>

      </div>
    </footer>
  );
};
