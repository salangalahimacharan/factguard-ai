import React, { useState } from 'react';
import { FactCheckResponse } from '../types';
import { VerdictBadge } from '../components/VerdictBadge';
import { getPdfDownloadUrl } from '../services/api';
import { 
  Download, ExternalLink, ShieldCheck, Scale, AlertTriangle, 
  CheckCircle, XCircle, HelpCircle, Layers, FileText, Info, ChevronDown, ChevronUp, Cpu
} from 'lucide-react';

interface ResultsDashboardPageProps {
  data: FactCheckResponse;
}

export const ResultsDashboardPage: React.FC<ResultsDashboardPageProps> = ({ data }) => {
  const [activeTab, setActiveTab] = useState<'claims' | 'sources' | 'bias' | 'agents'>('claims');
  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(data.extracted_claims[0]?.claim_id || null);

  // Compute Evidence Balance Metrics
  let totalSupporting = 0;
  let totalContradicting = 0;
  data.claim_verdicts.forEach(cv => {
    totalSupporting += cv.supporting_sources_count;
    totalContradicting += cv.contradicting_sources_count;
  });
  const totalEv = totalSupporting + totalContradicting || 1;
  const supportingPct = Math.round((totalSupporting / totalEv) * 100);
  const contradictingPct = 100 - supportingPct;

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-4 px-4">
      
      {/* HEADER ACTION BAR */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 glass-panel p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
              ID: {data.id.substring(0, 8)}
            </span>
            <span className="text-xs text-slate-400">
              {new Date(data.created_at).toLocaleString()}
            </span>
          </div>
          <h1 className="text-xl font-bold text-white leading-tight">
            FactGuard AI Verification Dashboard
          </h1>
        </div>

        <a
          href={getPdfDownloadUrl(data.id)}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold px-4 py-2.5 rounded-xl border border-slate-700 transition-all shadow-md"
        >
          <Download className="w-4 h-4 text-cyan-400" />
          <span>Export PDF Report</span>
        </a>
      </div>

      {/* TOP GRID: OVERALL VERDICT & EVIDENCE BALANCE */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* OVERALL VERDICT CARD */}
        <div className="md:col-span-2 glass-panel p-8 rounded-3xl border border-slate-800 shadow-2xl flex flex-col justify-between space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall Verdict</span>
              <div className="mt-2">
                <VerdictBadge verdict={data.overall_verdict} size="lg" />
              </div>
            </div>

            <div className="flex items-center space-x-4 bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
              <div className="text-center">
                <div className="text-2xl font-black text-white">{data.confidence_score}%</div>
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Confidence</div>
              </div>
              <div className="w-12 h-12 rounded-full border-4 border-cyan-500/40 flex items-center justify-center font-bold text-xs text-cyan-300">
                {data.confidence_score}%
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200">Executive Summary</h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              {data.summary}
            </p>
            {data.key_context && (
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
                <strong>Important Context:</strong> {data.key_context}
              </div>
            )}
          </div>
        </div>

        {/* EVIDENCE BALANCE VISUAL CARD */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 shadow-2xl space-y-6 flex flex-col justify-between">
          <div className="flex items-center space-x-2">
            <Scale className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Evidence Balance</h3>
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-emerald-400">Supporting Evidence</span>
                <span className="text-emerald-300">{supportingPct}%</span>
              </div>
              <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden p-0.5 border border-slate-800">
                <div className="bg-emerald-500 h-full rounded-full transition-all duration-500" style={{ width: `${supportingPct}%` }}></div>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-rose-400">Contradicting Evidence</span>
                <span className="text-rose-300">{contradictingPct}%</span>
              </div>
              <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden p-0.5 border border-slate-800">
                <div className="bg-rose-500 h-full rounded-full transition-all duration-500" style={{ width: `${contradictingPct}%` }}></div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-center text-xs pt-2 border-t border-slate-800">
            <div className="p-2 rounded-xl bg-slate-900/80">
              <div className="font-bold text-white text-base">{totalSupporting}</div>
              <div className="text-slate-400 text-[10px]">Supporting</div>
            </div>
            <div className="p-2 rounded-xl bg-slate-900/80">
              <div className="font-bold text-white text-base">{totalContradicting}</div>
              <div className="text-slate-400 text-[10px]">Contradicting</div>
            </div>
          </div>
        </div>

      </div>

      {/* DASHBOARD TABS NAVIGATION */}
      <div className="glass-panel p-1.5 rounded-2xl flex items-center justify-between border border-slate-800 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('claims')}
          className={`flex-1 py-3 rounded-xl transition-all flex items-center justify-center space-x-2 ${
            activeTab === 'claims' ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40 shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Extracted Claims ({data.extracted_claims.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('sources')}
          className={`flex-1 py-3 rounded-xl transition-all flex items-center justify-center space-x-2 ${
            activeTab === 'sources' ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40 shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          <ExternalLink className="w-4 h-4" />
          <span>Retrieved Sources ({data.sources.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('bias')}
          className={`flex-1 py-3 rounded-xl transition-all flex items-center justify-center space-x-2 ${
            activeTab === 'bias' ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40 shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Bias & Framing Analysis</span>
        </button>

        <button
          onClick={() => setActiveTab('agents')}
          className={`flex-1 py-3 rounded-xl transition-all flex items-center justify-center space-x-2 ${
            activeTab === 'agents' ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40 shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>Agent Activity Logs</span>
        </button>
      </div>

      {/* TAB CONTENT 1: EXTRACTED CLAIMS */}
      {activeTab === 'claims' && (
        <div className="space-y-4">
          {data.claim_verdicts.map((cv) => {
            const isExpanded = expandedClaimId === cv.claim_id;
            return (
              <div 
                key={cv.claim_id}
                className="glass-panel rounded-2xl border border-slate-800 overflow-hidden transition-all shadow-lg"
              >
                <div 
                  onClick={() => setExpandedClaimId(isExpanded ? null : cv.claim_id)}
                  className="p-6 flex items-start justify-between gap-4 cursor-pointer hover:bg-slate-900/40 transition-colors"
                >
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
                        {cv.claim_id}
                      </span>
                      <VerdictBadge verdict={cv.verdict} size="sm" />
                      <span className="text-xs text-slate-400 font-semibold">
                        Confidence: {cv.confidence_score}%
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-white leading-snug">
                      "{cv.claim_text}"
                    </h3>

                    <p className="text-xs text-slate-300">
                      {cv.explanation}
                    </p>
                  </div>

                  <button className="p-2 text-slate-400 hover:text-white">
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </button>
                </div>

                {isExpanded && (
                  <div className="p-6 bg-slate-950/80 border-t border-slate-800/80 space-y-6 text-xs">
                    
                    {/* Evidence breakdown */}
                    {cv.evidence_breakdown && (
                      <div className="space-y-3">
                        <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">Categorized Evidence Items</h4>
                        
                        {/* Supporting */}
                        {cv.evidence_breakdown.supporting_evidence.map((ev) => (
                          <div key={ev.evidence_id} className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-emerald-300 space-y-1">
                            <div className="font-bold text-emerald-200">✓ Supporting Evidence ({ev.publisher})</div>
                            <div>"{ev.evidence_text}"</div>
                            <a href={ev.source_url} target="_blank" rel="noreferrer" className="underline text-[10px] text-emerald-400 hover:text-emerald-300 inline-block pt-1">
                              View Primary Source →
                            </a>
                          </div>
                        ))}

                        {/* Contradicting */}
                        {cv.evidence_breakdown.contradicting_evidence.map((ev) => (
                          <div key={ev.evidence_id} className="p-3 rounded-xl bg-rose-950/30 border border-rose-800/40 text-rose-300 space-y-1">
                            <div className="font-bold text-rose-200">✗ Contradicting Evidence ({ev.publisher})</div>
                            <div>"{ev.evidence_text}"</div>
                            <a href={ev.source_url} target="_blank" rel="noreferrer" className="underline text-[10px] text-rose-400 hover:text-rose-300 inline-block pt-1">
                              View Primary Source →
                            </a>
                          </div>
                        ))}

                        {cv.evidence_breakdown.supporting_evidence.length === 0 && cv.evidence_breakdown.contradicting_evidence.length === 0 && (
                          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-400">
                            No direct supporting or contradicting excerpts found. Rated based on domain authority and background context.
                          </div>
                        )}
                      </div>
                    )}

                    {/* Consistency */}
                    {cv.consistency && (
                      <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 text-slate-300">
                        <div className="font-bold text-slate-200">Cross-Source Consistency Score: {cv.consistency.consistency_score}/100</div>
                        <div>{cv.consistency.findings}</div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* TAB CONTENT 2: RETRIEVED SOURCES */}
      {activeTab === 'sources' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.sources.map((src) => (
            <div key={src.source_id} className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-cyan-300 border border-slate-700">
                    {src.publisher}
                  </span>
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                    Credibility: {src.credibility_score}/100
                  </span>
                </div>

                <a 
                  href={src.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm font-bold text-white hover:text-cyan-300 transition-colors inline-flex items-center space-x-1.5"
                >
                  <span>{src.title}</span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0 text-cyan-400" />
                </a>

                <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                  "{src.excerpt}"
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                <span>Type: {src.source_type}</span>
                <span>{src.reliability_indicators[0] || 'Verified Domain'}</span>
              </div>
            </div>
          ))}

          {data.sources.length === 0 && (
            <div className="col-span-2 p-12 text-center glass-panel rounded-2xl text-slate-400 text-sm">
              No online sources could be retrieved for this submission.
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT 3: BIAS ANALYSIS */}
      {activeTab === 'bias' && data.bias_analysis && (
        <div className="glass-panel p-8 rounded-3xl border border-slate-800 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Linguistic Bias & Manipulation Report</h3>
              <p className="text-xs text-slate-400">Agent 5 framing analysis (Separated from factuality)</p>
            </div>

            <div className="text-right">
              <div className="text-2xl font-black text-amber-400">{data.bias_analysis.bias_score}/100</div>
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Bias Score</div>
            </div>
          </div>

          <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
            {data.bias_analysis.summary}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className={`p-4 rounded-2xl border ${data.bias_analysis.sensational_language ? 'bg-amber-950/40 border-amber-500/40 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-500'}`}>
              <div className="font-bold text-xs uppercase">Sensationalism</div>
              <div className="text-sm mt-1">{data.bias_analysis.sensational_language ? 'Detected' : 'Clean'}</div>
            </div>

            <div className={`p-4 rounded-2xl border ${data.bias_analysis.clickbait_framing ? 'bg-amber-950/40 border-amber-500/40 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-500'}`}>
              <div className="font-bold text-xs uppercase">Clickbait</div>
              <div className="text-sm mt-1">{data.bias_analysis.clickbait_framing ? 'Detected' : 'Clean'}</div>
            </div>

            <div className={`p-4 rounded-2xl border ${data.bias_analysis.emotional_manipulation ? 'bg-amber-950/40 border-amber-500/40 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-500'}`}>
              <div className="font-bold text-xs uppercase">Emotional Tone</div>
              <div className="text-sm mt-1">{data.bias_analysis.emotional_manipulation ? 'High' : 'Neutral'}</div>
            </div>

            <div className={`p-4 rounded-2xl border ${data.bias_analysis.missing_context ? 'bg-amber-950/40 border-amber-500/40 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-500'}`}>
              <div className="font-bold text-xs uppercase">Missing Context</div>
              <div className="text-sm mt-1">{data.bias_analysis.missing_context ? 'Detected' : 'None'}</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT 4: AGENT ACTIVITY LOGS */}
      {activeTab === 'agents' && (
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white">AI Agent Execution Audit Log</h3>
          <div className="space-y-3">
            {data.agent_logs.map((log, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
                <div className="space-y-1">
                  <div className="font-bold text-cyan-300">{log.agent_name}</div>
                  <div className="text-slate-400">{log.message}</div>
                </div>
                <div className="text-right font-mono shrink-0 ml-4">
                  <div className="text-slate-300">{log.execution_time_ms} ms</div>
                  <div className="text-[10px] text-emerald-400 capitalize">{log.status}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
