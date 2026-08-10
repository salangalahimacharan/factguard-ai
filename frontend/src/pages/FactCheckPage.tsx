import React, { useState } from 'react';
import { verifyText, verifyUrl, verifyImage } from '../services/api';
import { FactCheckResponse } from '../types';
import { AgentProgressTracker, AGENT_STEPS } from '../components/AgentProgressTracker';
import { ResultsDashboardPage } from './ResultsDashboardPage';
import { Search, Link as LinkIcon, Image as ImageIcon, Upload, Loader2, AlertCircle, ArrowLeft } from 'lucide-react';

export const FactCheckPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'text' | 'url' | 'image'>('text');
  const [inputText, setInputText] = useState('');
  const [inputUrl, setInputUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<FactCheckResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsLoading(true);
    setCurrentStep(0);

    // Simulate progressive step timing for agent progress visualization
    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < AGENT_STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 700);

    try {
      let res: FactCheckResponse;
      if (activeTab === 'text') {
        if (!inputText.trim()) throw new Error('Please enter text to verify.');
        res = await verifyText(inputText);
      } else if (activeTab === 'url') {
        if (!inputUrl.trim()) throw new Error('Please enter a valid URL.');
        res = await verifyUrl(inputUrl);
      } else {
        if (!selectedFile) throw new Error('Please select an image file to upload.');
        res = await verifyImage(selectedFile);
      }

      clearInterval(stepInterval);
      setCurrentStep(AGENT_STEPS.length);
      setResult(res);
    } catch (err: any) {
      clearInterval(stepInterval);
      setErrorMsg(err.message || 'An error occurred during verification.');
    } finally {
      setIsLoading(false);
    }
  };

  if (result) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setResult(null)}
          className="inline-flex items-center space-x-2 text-sm text-cyan-400 hover:text-cyan-300 font-medium glass-panel px-4 py-2 rounded-xl border border-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Verify Another Claim</span>
        </button>
        <ResultsDashboardPage data={result} />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 py-6 px-4">
      
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Fact-Check Workspace
        </h1>
        <p className="text-slate-400 text-sm">
          Submit raw text, news article URL, or social media screenshot image for evidence evaluation.
        </p>
      </div>

      {/* Input Switcher Tabs */}
      <div className="glass-panel p-1.5 rounded-2xl flex items-center justify-between border border-slate-800">
        <button
          type="button"
          onClick={() => setActiveTab('text')}
          className={`flex-1 flex items-center justify-center space-x-2 py-3 rounded-xl text-sm font-semibold transition-all ${
            activeTab === 'text' ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-500/40 shadow-lg' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Search className="w-4 h-4" />
          <span>Text Input</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('url')}
          className={`flex-1 flex items-center justify-center space-x-2 py-3 rounded-xl text-sm font-semibold transition-all ${
            activeTab === 'url' ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-500/40 shadow-lg' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <LinkIcon className="w-4 h-4" />
          <span>URL Link</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('image')}
          className={`flex-1 flex items-center justify-center space-x-2 py-3 rounded-xl text-sm font-semibold transition-all ${
            activeTab === 'image' ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-500/40 shadow-lg' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ImageIcon className="w-4 h-4" />
          <span>Image OCR</span>
        </button>
      </div>

      {/* Verification Form */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {activeTab === 'text' && (
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Claim or Social Media Post Content
              </label>
              <textarea
                rows={5}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Paste the tweet, post, news claim, or statement here to verify... e.g. Company X launched a new AI model in January 2026 that is 50% faster than Model Y."
                className="w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/60 text-sm leading-relaxed"
                disabled={isLoading}
              />
            </div>
          )}

          {activeTab === 'url' && (
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Article or Social Media Post URL
              </label>
              <input
                type="url"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                placeholder="https://news.example.com/article/12345"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/60 text-sm"
                disabled={isLoading}
              />
            </div>
          )}

          {activeTab === 'image' && (
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Upload Post Screenshot (OCR Text Extraction)
              </label>
              <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-2xl p-8 text-center bg-slate-900/40 cursor-pointer transition-colors">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="image-upload"
                  disabled={isLoading}
                />
                <label htmlFor="image-upload" className="cursor-pointer space-y-2 flex flex-col items-center">
                  <Upload className="w-8 h-8 text-cyan-400" />
                  <span className="text-sm text-slate-300 font-medium">
                    {selectedFile ? selectedFile.name : 'Click or drop image screenshot here'}
                  </span>
                  <span className="text-xs text-slate-500">Supports PNG, JPG, WebP up to 10MB</span>
                </label>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 disabled:opacity-50 text-white font-bold text-base py-4 rounded-2xl shadow-xl shadow-cyan-500/20 flex items-center justify-center space-x-2 transition-all"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Executing Multi-Agent Pipeline...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                <span>Verify Now</span>
              </>
            )}
          </button>

        </form>
      </div>

      {/* Real-time Agent Progress Tracker */}
      {isLoading && (
        <div className="pt-4">
          <AgentProgressTracker currentStepIndex={currentStep} />
        </div>
      )}

    </div>
  );
};
