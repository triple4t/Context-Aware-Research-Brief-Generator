'use client';

import { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/api';
import { UserHistory } from '../../types';
import { ChartBarIcon, DocumentTextIcon, CalendarIcon, GlobeAltIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

export default function History() {
  const [history, setHistory] = useState<UserHistory | null>(null);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await apiClient.getUserHistory(userId, 20);
        setHistory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [userId]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl shadow-xl p-8 text-white">
          <div className="flex items-center space-x-4">
            <div className="bg-white/20 rounded-xl p-3">
              <ChartBarIcon className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Research History</h1>
              <p className="text-indigo-100 text-lg">View your past research briefs and analysis</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <p className="text-red-700 font-medium">{error}</p>
          </div>
        )}

        {!history?.briefs || history.briefs.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-12">
            <div className="text-center">
              <div className="bg-gradient-to-r from-indigo-100 to-purple-100 rounded-2xl p-8 max-w-md mx-auto">
                <DocumentTextIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">No research history</h3>
                <p className="text-gray-600 mb-6">You haven&apos;t generated any research briefs yet.</p>
                <a
                  href="/brief"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-sm font-medium rounded-xl shadow-lg text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200"
                >
                  Generate Your First Brief
                </a>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {history.briefs.map((brief, index) => (
              <div key={`brief-${brief.id}-${index}`} className="bg-white rounded-2xl shadow-xl border border-gray-100 hover:shadow-2xl transition-shadow duration-300">
                <div className="p-8">
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{brief.topic}</h3>

                      <div className="flex items-center space-x-6 text-sm text-gray-500 mb-4">
                        <div className="flex items-center space-x-2">
                          <CalendarIcon className="h-4 w-4" />
                          <span className="font-medium">{formatDate(brief.generated_at)}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <GlobeAltIcon className="h-4 w-4" />
                          <span className="font-medium">{brief.references.length} sources</span>
                        </div>
                      </div>

                      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 mb-6 border border-indigo-100">
                        <p className="text-gray-700 leading-relaxed">
                          {brief.executive_summary.length > 300
                            ? `${brief.executive_summary.substring(0, 300)}...`
                            : brief.executive_summary}
                        </p>
                      </div>

                      <div className="space-y-3">
                        <h4 className="text-sm font-semibold text-gray-900">Key Insights:</h4>
                        <div className="space-y-2">
                          {brief.key_insights.slice(0, 3).map((insight, insightIndex) => (
                            <div key={`insight-${brief.id}-${index}-${insightIndex}`} className="flex items-start space-x-3 bg-gray-50 rounded-xl p-3">
                              <span className="bg-indigo-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{insightIndex + 1}</span>
                              <span className="text-sm text-gray-700">{insight}</span>
                            </div>
                          ))}
                          {brief.key_insights.length > 3 && (
                            <div className="text-sm text-gray-500 bg-gray-100 rounded-xl p-3">
                              ... and {brief.key_insights.length - 3} more insights
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="pt-6 border-t border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-6 text-sm text-gray-500">
                        <span className="bg-gray-100 px-3 py-1 rounded-full font-medium">ID: {brief.id}</span>
                        <span className="font-medium">Generated: {formatDate(brief.generated_at)}</span>
                      </div>
                      <button
                        onClick={() => {
                          const dataStr = JSON.stringify(brief, null, 2);
                          const dataBlob = new Blob([dataStr], { type: 'application/json' });
                          const url = URL.createObjectURL(dataBlob);
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = `brief_${brief.id}_${new Date(brief.generated_at).toISOString().slice(0, 10)}.json`;
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                          URL.revokeObjectURL(url);
                        }}
                        className="inline-flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-2 rounded-xl hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 shadow-lg transition-all duration-200 font-medium"
                      >
                        <ArrowDownTrayIcon className="h-4 w-4" />
                        <span>Download</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
} 