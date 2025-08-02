'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { UserStats, HealthCheck } from '@/types';
import {
  DocumentTextIcon,
  ClockIcon,
  GlobeAltIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  XCircleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

export default function Dashboard() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [loading, setLoading] = useState(true);
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
    const fetchData = async () => {
      try {
        const [statsData, healthData] = await Promise.all([
          apiClient.getUserStats(userId),
          apiClient.healthCheck(),
        ]);
        setStats(statsData);
        setHealth(healthData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [userId]);

  const metrics = [
    {
      name: 'Total Briefs',
      value: stats?.stats.total_briefs || 0,
      icon: DocumentTextIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      gradient: 'from-blue-500 to-blue-600',
    },
    {
      name: 'Avg Time',
      value: `${(stats?.stats.average_execution_time || 0).toFixed(1)}s`,
      icon: ClockIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      gradient: 'from-green-500 to-green-600',
    },
    {
      name: 'Sources Used',
      value: stats?.stats.total_sources || 0,
      icon: GlobeAltIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      gradient: 'from-purple-500 to-purple-600',
    },
    {
      name: 'Total Cost',
      value: `$${(stats?.stats.total_cost_estimate || 0).toFixed(2)}`,
      icon: CurrencyDollarIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      gradient: 'from-orange-500 to-orange-600',
    },
  ];

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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Welcome to Research Brief Generator</h1>
              <p className="text-indigo-100 text-lg">Powered by Azure OpenAI & LangGraph</p>
            </div>
            <div className="flex items-center space-x-2">
              {health?.status === 'healthy' ? (
                <CheckCircleIcon className="h-8 w-8 text-green-400" />
              ) : (
                <XCircleIcon className="h-8 w-8 text-red-400" />
              )}
              <span className="text-indigo-100 font-medium">
                {health?.status === 'healthy' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.name} className="bg-white overflow-hidden shadow-lg rounded-xl border border-gray-100 hover:shadow-xl transition-shadow duration-300">
              <div className="p-6">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 bg-gradient-to-r ${metric.gradient} rounded-xl p-3 shadow-lg`}>
                    <metric.icon className="h-8 w-8 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">{metric.name}</dt>
                      <dd className="text-2xl font-bold text-gray-900">{metric.value}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="bg-white shadow-lg rounded-2xl border border-gray-100">
          <div className="p-8">
            <div className="flex items-center mb-6">
              <SparklesIcon className="h-8 w-8 text-indigo-600 mr-3" />
              <h2 className="text-2xl font-bold text-gray-900">Quick Actions</h2>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <a
                href="/brief"
                className="group relative rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-lg transition-all duration-200 hover:border-indigo-300 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-lg p-3 shadow-lg">
                      <DocumentTextIcon className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="absolute inset-0" aria-hidden="true" />
                    <p className="text-lg font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">Generate Brief</p>
                    <p className="text-sm text-gray-500">Create a new research brief</p>
                  </div>
                </div>
              </a>

              <a
                href="/history"
                className="group relative rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-lg transition-all duration-200 hover:border-purple-300 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-purple-500"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-3 shadow-lg">
                      <DocumentTextIcon className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="absolute inset-0" aria-hidden="true" />
                    <p className="text-lg font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">View History</p>
                    <p className="text-sm text-gray-500">See your past briefs</p>
                  </div>
                </div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
