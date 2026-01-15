'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart3, TrendingUp, Users, FileText, Phone,
  Download, Eye, RefreshCw
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';

export default function AdminLeadPagesMetrics() {
  const [overview, setOverview] = useState<any>(null);
  const [daily, setDaily] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [funnel, setFunnel] = useState<any>(null);
  const [recent, setRecent] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const [ov, dy, ag, dv, fn, rc] = await Promise.all([
        fetch('/api/proxy/v1/admin/metrics/overview').then(r => r.json()),
        fetch('/api/proxy/v1/admin/metrics/daily?days=30').then(r => r.json()),
        fetch('/api/proxy/v1/admin/metrics/agents?limit=10').then(r => r.json()),
        fetch('/api/proxy/v1/admin/metrics/devices').then(r => r.json()),
        fetch('/api/proxy/v1/admin/metrics/conversion-funnel').then(r => r.json()),
        fetch('/api/proxy/v1/admin/metrics/recent?limit=10').then(r => r.json()),
      ]);
      setOverview(ov);
      setDaily(Array.isArray(dy) ? dy.reverse() : []);
      setAgents(Array.isArray(ag) ? ag : []);
      setDevices(Array.isArray(dv) ? dv : []);
      setFunnel(fn);
      setRecent(Array.isArray(rc) ? rc : []);
    } catch (err) {
      console.error('Failed to fetch metrics', err);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#8B5CF6', '#EC4899', '#F59E0B', '#10B981'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-600" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lead Pages Analytics</h1>
          <p className="text-gray-600">Consumer report performance metrics</p>
        </div>
        <Button onClick={fetchMetrics} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          icon={<FileText className="w-5 h-5" />}
          label="Total Reports"
          value={overview?.total_reports?.toLocaleString() || '0'}
          subtext={`${overview?.reports_today || 0} today`}
        />
        <MetricCard
          icon={<Eye className="w-5 h-5" />}
          label="Total Views"
          value={overview?.total_views?.toLocaleString() || '0'}
          subtext={`${overview?.views_today || 0} today`}
        />
        <MetricCard
          icon={<Phone className="w-5 h-5" />}
          label="Agent Contacts"
          value={overview?.total_contacts?.toLocaleString() || '0'}
          subtext={`${overview?.contact_rate_pct || 0}% rate`}
          highlight
        />
        <MetricCard
          icon={<Download className="w-5 h-5" />}
          label="PDFs Generated"
          value={overview?.total_pdfs?.toLocaleString() || '0'}
          subtext={`${overview?.pdf_rate_pct || 0}% of reports`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Daily Trend */}
        <Card className="p-4">
          <h3 className="font-semibold mb-4">Reports & Contacts (30 Days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="reports_requested" 
                  stroke="#8B5CF6" 
                  strokeWidth={2}
                  name="Reports"
                />
                <Line 
                  type="monotone" 
                  dataKey="agent_contacts" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  name="Contacts"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Device Breakdown */}
        <Card className="p-4">
          <h3 className="font-semibold mb-4">Device Breakdown</h3>
          <div className="h-64 flex items-center justify-center">
            {devices.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={devices}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    dataKey="count"
                    nameKey="device_type"
                    label={({ device_type, percentage }) => `${device_type} ${percentage}%`}
                  >
                    {devices.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500">No data yet</p>
            )}
          </div>
        </Card>
      </div>

      {/* Conversion Funnel */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Conversion Funnel (30 Days)</h3>
        <div className="grid grid-cols-6 gap-2">
          {funnel?.funnel?.map((step: any, i: number) => (
            <div 
              key={i}
              className="text-center p-3 rounded-lg"
              style={{ 
                backgroundColor: `rgba(139, 92, 246, ${0.1 + (step.pct / 100) * 0.3})` 
              }}
            >
              <p className="text-2xl font-bold text-violet-700">{step.count}</p>
              <p className="text-xs text-gray-600 mt-1">{step.stage}</p>
              <p className="text-xs text-violet-600 font-medium">{step.pct}%</p>
            </div>
          )) || <p className="col-span-6 text-center text-gray-500">No data yet</p>}
        </div>
      </Card>

      {/* Agent Leaderboard */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Top Agents by Reports</h3>
        <div className="overflow-x-auto">
          {agents.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-gray-500 border-b">
                  <th className="pb-2">Agent</th>
                  <th className="pb-2">Account</th>
                  <th className="pb-2 text-right">Reports</th>
                  <th className="pb-2 text-right">Views</th>
                  <th className="pb-2 text-right">Contacts</th>
                  <th className="pb-2 text-right">Rate</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((agent, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-3">
                      <p className="font-medium">{agent.agent_name}</p>
                      <p className="text-sm text-gray-500">{agent.agent_email}</p>
                    </td>
                    <td className="py-3 text-gray-600">{agent.account_name}</td>
                    <td className="py-3 text-right font-medium">{agent.total_reports}</td>
                    <td className="py-3 text-right">{agent.total_views}</td>
                    <td className="py-3 text-right">{agent.contacts}</td>
                    <td className="py-3 text-right">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        agent.contact_rate_pct >= 10 
                          ? 'bg-green-100 text-green-700'
                          : agent.contact_rate_pct >= 5
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {agent.contact_rate_pct}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-center text-gray-500 py-4">No agents with reports yet</p>
          )}
        </div>
      </Card>

      {/* Recent Activity */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Recent Reports</h3>
        <div className="space-y-2">
          {recent.length > 0 ? (
            recent.map((report, i) => (
              <div 
                key={i}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{report.property_address}</p>
                  <p className="text-sm text-gray-500">{report.agent_name}</p>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    report.status === 'ready' 
                      ? 'bg-green-100 text-green-700'
                      : report.status === 'failed'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {report.status}
                  </span>
                  <span className="text-gray-500">{report.view_count} views</span>
                  {report.agent_contacted && (
                    <Phone className="w-4 h-4 text-green-600" />
                  )}
                  {report.has_pdf && (
                    <Download className="w-4 h-4 text-violet-600" />
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-500 py-4">No reports yet</p>
          )}
        </div>
      </Card>
    </div>
  );
}


function MetricCard({ 
  icon, 
  label, 
  value, 
  subtext,
  highlight 
}: { 
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext?: string;
  highlight?: boolean;
}) {
  return (
    <Card className={`p-4 ${highlight ? 'ring-2 ring-violet-200 bg-violet-50' : ''}`}>
      <div className="flex items-center gap-2 text-gray-600 mb-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {subtext && (
        <p className="text-sm text-gray-500 mt-1">{subtext}</p>
      )}
    </Card>
  );
}

