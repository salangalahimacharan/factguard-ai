import React, { useEffect, useState } from 'react';
import { getFactCheckHistory, getFactCheckById } from '../services/api';
import { FactCheckHistoryItem, FactCheckResponse } from '../types';
import { VerdictBadge } from '../components/VerdictBadge';
import { ResultsDashboardPage } from './ResultsDashboardPage';
import { History, Search, ArrowRight, Loader2, ArrowLeft } from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<FactCheckHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedReport, setSelectedReport] = useState<FactCheckResponse | null>(null);
  const [isFetchingReport, setIsFetchingReport] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const items = await getFactCheckHistory();
      setHistory(items);
    } catch (e) {
      console.error('History fetch error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenReport = async (id: string) => {
    setIsFetchingReport(true);
    try {
      const report = await getFactCheckById(id);
      setSelectedReport(report);
    } catch (err) {
      alert('Could not retrieve target fact check report.');
    } finally {
      setIsFetchingReport(false);
    }
  };

  if (selectedReport) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setSelectedReport(null)}
          className="inline-flex items-center space-x-2 text-sm text-cyan-400 hover:text-cyan-300 font-medium glass-panel px-4 py-2 rounded-xl border border-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Verification History</span>
        </button>
        <ResultsDashboardPage data={selectedReport} />
      </div>
    );
  }

  const filteredHistory = history.filter(item => 
    item.original_input.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.overall_verdict.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8 py-6 px-4">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Verification History</h1>
          <p className="text-slate-400 text-sm">View past multi-agent fact check reports and evidence logs.</p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search history..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 text-center glass-panel rounded-3xl space-y-3">
          <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">Loading historical reports...</p>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="p-12 text-center glass-panel rounded-3xl space-y-3 text-slate-400">
          <History className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-base font-bold text-slate-300">No Fact Checks Recorded Yet</p>
          <p className="text-xs">Submit a claim on the Check Claim page to generate your first evidence report.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredHistory.map((item) => (
            <div
              key={item.id}
              onClick={() => handleOpenReport(item.id)}
              className="glass-panel p-6 rounded-2xl border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all flex items-center justify-between gap-4 group"
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center space-x-3">
                  <VerdictBadge verdict={item.overall_verdict} size="sm" />
                  <span className="text-xs text-slate-400 font-semibold">
                    Confidence: {item.confidence_score}%
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>

                <p className="text-sm font-semibold text-white group-hover:text-cyan-300 transition-colors line-clamp-2">
                  "{item.original_input}"
                </p>
              </div>

              <div className="flex items-center space-x-2 text-xs font-semibold text-cyan-400 group-hover:translate-x-1 transition-transform shrink-0">
                <span>Open Report</span>
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};
