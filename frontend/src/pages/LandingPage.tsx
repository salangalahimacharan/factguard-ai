import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, Search, Cpu, Database, FileText, CheckCircle2, 
  ArrowRight, Scale, AlertTriangle, Layers, Lock, Sparkles 
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-24 py-8">
      
      {/* HERO SECTION */}
      <section className="relative text-center space-y-8 max-w-4xl mx-auto px-4 pt-12">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-cyan-300 text-xs font-semibold shadow-lg shadow-cyan-950/40">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Evidence-First Multi-Agent Fact Verification</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-tight">
          Verify Social Media Information with <span className="gradient-text">Empirical Evidence</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto font-normal leading-relaxed">
          FactGuard AI deploys a coordinated network of 7 specialized AI agents to extract claims, retrieve live web sources, evaluate publisher credibility, and produce transparent verdicts.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            to="/verify"
            className="w-full sm:w-auto bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-bold text-base px-8 py-4 rounded-2xl shadow-xl shadow-cyan-500/25 flex items-center justify-center space-x-2 transition-all transform hover:-translate-y-0.5"
          >
            <Search className="w-5 h-5" />
            <span>Check a Claim Now</span>
            <ArrowRight className="w-5 h-5" />
          </Link>

          <Link
            to="/demo"
            className="w-full sm:w-auto glass-panel hover:bg-slate-800/80 text-slate-200 font-semibold text-base px-8 py-4 rounded-2xl border border-slate-700 flex items-center justify-center space-x-2 transition-all"
          >
            <Layers className="w-5 h-5 text-cyan-400" />
            <span>Faculty Demo Mode</span>
          </Link>
        </div>

        {/* Quick Features Badges */}
        <div className="pt-8 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-medium text-slate-400">
          <div className="glass-card p-3 rounded-xl flex items-center justify-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>No LLM Hallucinations</span>
          </div>
          <div className="glass-card p-3 rounded-xl flex items-center justify-center space-x-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <span>ChromaDB Vector RAG</span>
          </div>
          <div className="glass-card p-3 rounded-xl flex items-center justify-center space-x-2">
            <Lock className="w-4 h-4 text-indigo-400" />
            <span>Prompt Injection Guard</span>
          </div>
          <div className="glass-card p-3 rounded-xl flex items-center justify-center space-x-2">
            <Scale className="w-4 h-4 text-amber-400" />
            <span>Source Credibility 0-100</span>
          </div>
        </div>
      </section>

      {/* MULTI-AGENT ARCHITECTURE SECTION */}
      <section className="max-w-7xl mx-auto px-4 space-y-12">
        <div className="text-center space-y-3">
          <h2 className="text-3xl font-extrabold text-white">7-Agent AI Investigation Architecture</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Instead of asking a single chatbot, FactGuard AI delegates tasks to autonomous specialized agents in a stateful execution graph.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <div className="glass-card p-6 rounded-2xl space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-cyan-950 text-cyan-400 flex items-center justify-center font-bold text-sm">A1</div>
            <h3 className="text-lg font-bold text-white">Claim Extraction</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Parses raw input text, separates opinions from verifiable statements, and creates atomic claim IDs with entity tagging.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-sky-950 text-sky-400 flex items-center justify-center font-bold text-sm">A2</div>
            <h3 className="text-lg font-bold text-white">Web Researcher</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Executes multi-query web searches across primary sources, academic registries, and official databases without fabricating URLs.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-indigo-950 text-indigo-400 flex items-center justify-center font-bold text-sm">A3</div>
            <h3 className="text-lg font-bold text-white">Evidence Verification</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Categorizes evidence chunks into supporting, contradicting, and contextual data with quantitative strength metrics.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-emerald-950 text-emerald-400 flex items-center justify-center font-bold text-sm">A4</div>
            <h3 className="text-lg font-bold text-white">Source Credibility</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Scores web sources from 0-100 based on TLD authority (.gov, .edu), primary publisher track record, and direct relevance.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-amber-950 text-amber-400 flex items-center justify-center font-bold text-sm">A5</div>
            <h3 className="text-lg font-bold text-white">Bias & Manipulation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Detects sensationalism, clickbait, fear-mongering, and cherry-picked stats while separating tone from factuality.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all">
            <div className="w-10 h-10 rounded-xl bg-purple-950 text-purple-400 flex items-center justify-center font-bold text-sm">A6</div>
            <h3 className="text-lg font-bold text-white">Consistency Checker</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Corroborates independent publishers to verify agreement or detect single-source echo chambers.
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl space-y-3 border border-slate-800 hover:border-cyan-500/40 transition-all col-span-1 md:col-span-2">
            <div className="w-10 h-10 rounded-xl bg-rose-950 text-rose-400 flex items-center justify-center font-bold text-sm">A7</div>
            <h3 className="text-lg font-bold text-white">Final Judge Agent</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Issues transparent verdicts (VERIFIED, FALSE, MISLEADING, INSUFFICIENT EVIDENCE) backed by explicit citations.
            </p>
          </div>

        </div>
      </section>

      {/* EVIDENCE FIRST PRINCIPLE BANNER */}
      <section className="max-w-5xl mx-auto px-4">
        <div className="glass-panel p-8 rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-slate-900 via-cyan-950/20 to-slate-900 space-y-4 text-center">
          <Scale className="w-10 h-10 text-cyan-400 mx-auto" />
          <h2 className="text-2xl font-bold text-white">Strict Evidence-First Principle</h2>
          <p className="text-slate-300 text-sm max-w-2xl mx-auto leading-relaxed">
            If reliable online evidence cannot be retrieved to support or refute a claim, FactGuard AI strictly outputs:
          </p>
          <div className="inline-block px-4 py-2 rounded-xl bg-slate-950 border border-slate-700 font-mono text-cyan-300 text-sm font-bold shadow-inner">
            "INSUFFICIENT EVIDENCE to determine the claim."
          </div>
          <p className="text-xs text-slate-400">
            We never force a True/False answer without empirical backing.
          </p>
        </div>
      </section>

    </div>
  );
};
