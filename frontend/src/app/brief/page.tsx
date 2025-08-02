'use client';

import { useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/api';
import { BriefResponse } from '../../types';
import { DocumentTextIcon, CheckCircleIcon, XCircleIcon, SparklesIcon } from '@heroicons/react/24/outline';

export default function BriefGenerator() {
  const [formData, setFormData] = useState({
    topic: '',
    depth: 'moderate' as 'shallow' | 'moderate' | 'deep',
    followUp: false,
    additionalContext: '',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BriefResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userId] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('userId');
      if (stored) return stored;
      const newId = crypto.randomUUID();
      localStorage.setItem('userId', newId);
      return newId;
    }
    return crypto.randomUUID();
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.topic.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.generateBrief({
        topic: formData.topic.trim(),
        depth: formData.depth,
        user_id: userId,
        follow_up: formData.followUp,
        additional_context: formData.additionalContext.trim() || undefined,
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while generating the brief');
    } finally {
      setLoading(false);
    }
  };

  const downloadBrief = () => {
    if (!result) return;

    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `research_brief_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl shadow-xl p-8 text-white">
          <div className="flex items-center space-x-4">
            <div className="bg-white/20 rounded-xl p-3">
              <DocumentTextIcon className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Research Brief Generator</h1>
              <p className="text-indigo-100 text-lg">Generate comprehensive research briefs with AI-powered analysis</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
            <div className="flex items-center mb-6">
              <SparklesIcon className="h-8 w-8 text-indigo-600 mr-3" />
              <h2 className="text-2xl font-bold text-gray-900">Generate New Brief</h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="topic" className="block text-sm font-semibold text-gray-700 mb-3">
                  Research Topic *
                </label>
                <textarea
                  id="topic"
                  value={formData.topic}
                  onChange={(e) => setFormData(prev => ({ ...prev, topic: e.target.value }))}
                  placeholder="e.g., Impact of artificial intelligence on healthcare delivery in rural areas"
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm"
                  rows={4}
                  required
                />
              </div>

              <div>
                <label htmlFor="depth" className="block text-sm font-semibold text-gray-700 mb-3">
                  Research Depth
                </label>
                <select
                  id="depth"
                  value={formData.depth}
                  onChange={(e) => setFormData(prev => ({ ...prev, depth: e.target.value as 'shallow' | 'moderate' | 'deep' }))}
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm"
                >
                  <option value="shallow">🔍 Shallow (3-5 sources)</option>
                  <option value="moderate">📊 Moderate (5-8 sources)</option>
                  <option value="deep">🔬 Deep (8-12 sources)</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  id="followUp"
                  type="checkbox"
                  checked={formData.followUp}
                  onChange={(e) => setFormData(prev => ({ ...prev, followUp: e.target.checked }))}
                  className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="followUp" className="ml-3 block text-sm font-medium text-gray-900">
                  This is a follow-up query
                </label>
              </div>

              <div>
                <label htmlFor="additionalContext" className="block text-sm font-semibold text-gray-700 mb-3">
                  Additional Context (Optional)
                </label>
                <textarea
                  id="additionalContext"
                  value={formData.additionalContext}
                  onChange={(e) => setFormData(prev => ({ ...prev, additionalContext: e.target.value }))}
                  placeholder="Any specific requirements, focus areas, or context..."
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm"
                  rows={3}
                />
              </div>

              <button
                type="submit"
                disabled={loading || !formData.topic.trim()}
                className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-4 rounded-xl hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3 shadow-lg transition-all duration-200 font-semibold text-lg"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                    <span>Generating Brief...</span>
                  </>
                ) : (
                  <>
                    <DocumentTextIcon className="h-6 w-6" />
                    <span>Generate Research Brief</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Results */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Results</h2>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <div className="flex items-center space-x-3">
                  <XCircleIcon className="h-6 w-6 text-red-500" />
                  <p className="text-red-700 font-medium">{error}</p>
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                {/* Success Message */}
                <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                  <div className="flex items-center space-x-3">
                    <CheckCircleIcon className="h-6 w-6 text-green-500" />
                    <p className="text-green-700 font-medium">Research brief generated successfully!</p>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl p-4">
                    <p className="text-2xl font-bold text-blue-600">{result.execution_time.toFixed(1)}s</p>
                    <p className="text-sm text-blue-600 font-medium">Execution Time</p>
                  </div>
                  <div className="text-center bg-gradient-to-r from-green-50 to-green-100 rounded-xl p-4">
                    <p className="text-2xl font-bold text-green-600">{result.brief.references.length}</p>
                    <p className="text-sm text-green-600 font-medium">Sources</p>
                  </div>
                  <div className="text-center bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl p-4">
                    <p className="text-2xl font-bold text-purple-600">{result.token_usage?.total_tokens || 'N/A'}</p>
                    <p className="text-sm text-purple-600 font-medium">Tokens</p>
                  </div>
                </div>

                {/* Download Button */}
                <button
                  onClick={downloadBrief}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-3 rounded-xl hover:from-green-700 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 shadow-lg transition-all duration-200 font-semibold"
                >
                  Download Brief (JSON)
                </button>
              </div>
            )}

            {!result && !error && !loading && (
              <div className="text-center text-gray-500 py-12">
                <div className="bg-gradient-to-r from-indigo-100 to-purple-100 rounded-2xl p-8">
                  <DocumentTextIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">No brief generated yet</h3>
                  <p className="text-gray-600">Fill out the form and click &quot;Generate Research Brief&quot; to get started</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Brief Display */}
        {result && (
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100">
            <div className="p-8 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Generated Brief</h2>
            </div>

            <div className="p-8 space-y-8">
              {/* Topic Summary */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Research Topic</h3>
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                  <p className="text-lg font-medium text-gray-900">{formData.topic}</p>
                </div>
              </div>

              {/* Executive Summary */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Executive Summary</h3>
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100">
                  <p className="text-gray-700 leading-relaxed text-lg">{result.brief.executive_summary}</p>
                </div>
              </div>

              {/* Key Insights */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Key Insights</h3>
                <div className="space-y-3">
                  {result.brief.key_insights.map((insight, index) => (
                    <div key={`insight-${index}`} className="flex items-start space-x-3 bg-gray-50 rounded-xl p-4">
                      <span className="bg-indigo-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">{index + 1}</span>
                      <span className="text-gray-700">{insight}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Research Overview */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Research Overview</h3>
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-100">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">{result.brief.references.length}</p>
                      <p className="text-sm text-green-600 font-medium">Sources Analyzed</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">{result.execution_time.toFixed(1)}s</p>
                      <p className="text-sm text-blue-600 font-medium">Processing Time</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-600">{result.token_usage?.total_tokens || 'N/A'}</p>
                      <p className="text-sm text-purple-600 font-medium">AI Tokens Used</p>
                    </div>
                  </div>
                  <p className="text-gray-700 leading-relaxed">
                    This research brief provides a comprehensive analysis based on {result.brief.references.length} carefully selected sources.
                    The analysis covers key aspects of the topic and provides actionable insights for further research and decision-making.
                  </p>
                </div>
              </div>

              {/* Detailed Synthesis */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Detailed Synthesis</h3>
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100">
                  <p className="text-gray-700 leading-relaxed">{result.brief.synthesis}</p>
                </div>
              </div>

              {/* References */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">References & Sources</h3>
                <div className="space-y-4">
                  {result.brief.references.map((ref, index) => (
                    <div key={`ref-${index}`} className="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 mb-2">{ref.title}</h4>
                          <a
                            href={ref.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-indigo-600 mb-2 hover:text-indigo-800 underline break-all"
                          >
                            {ref.url}
                          </a>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>Relevance: {ref.relevance_score.toFixed(2)}</span>
                            <span>Type: {ref.source_type}</span>
                            {ref.publication_date && (
                              <span>Date: {ref.publication_date}</span>
                            )}
                          </div>
                        </div>
                        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">#{index + 1}</span>
                      </div>
                      <p className="text-sm text-gray-700 mb-3">{ref.summary}</p>
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-2">Key Points:</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {ref.key_points.map((point, pointIndex) => (
                            <li key={`point-${index}-${pointIndex}`} className="flex items-start space-x-2">
                              <span className="text-indigo-600 mt-1">•</span>
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
} 