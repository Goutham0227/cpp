import { useState, useEffect, useRef } from 'react';
import { Users, FolderOpen, Clock, DollarSign, Timer, Square, Play, Bell } from 'lucide-react';
import toast from 'react-hot-toast';
import * as api from '../api.js';

export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timerProject, setTimerProject] = useState('');
  const [timerDesc, setTimerDesc] = useState('');
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [subEmail, setSubEmail] = useState('');
  const [subscribing, setSubscribing] = useState(false);
  const [subCount, setSubCount] = useState(0);
  const intervalRef = useRef(null);

  const fetchData = async () => {
    try {
      const [dashRes, projRes, subRes] = await Promise.all([
        api.getDashboard(),
        api.getProjects(),
        api.getSubscriberCount().catch(() => ({ data: { count: 0 } })),
      ]);
      setDashboard(dashRes.data);
      setProjects(projRes.data.projects || projRes.data || []);
      setSubCount(subRes.data.count || 0);
    } catch (err) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (dashboard?.activeTimer) {
      const startTime = new Date(dashboard.activeTimer.startTime).getTime();
      const updateElapsed = () => {
        setElapsed(Math.floor((Date.now() - startTime) / 1000));
      };
      updateElapsed();
      intervalRef.current = setInterval(updateElapsed, 1000);
      return () => clearInterval(intervalRef.current);
    } else {
      setElapsed(0);
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
  }, [dashboard?.activeTimer]);

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleStart = async () => {
    if (!timerProject) return toast.error('Select a project');
    setStarting(true);
    try {
      await api.startTimer({ projectId: timerProject, description: timerDesc });
      toast.success('Timer started!');
      setTimerDesc('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to start timer');
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    if (!dashboard?.activeTimer) return;
    setStopping(true);
    try {
      await api.stopTimer(dashboard.activeTimer._id || dashboard.activeTimer.id);
      toast.success('Timer stopped!');
      fetchData();
    } catch (err) {
      toast.error('Failed to stop timer');
    } finally {
      setStopping(false);
    }
  };

  const handleSubscribe = async (e) => {
    e.preventDefault();
    setSubscribing(true);
    try {
      await api.subscribe({ email: subEmail });
      toast.success('Subscribed successfully!');
      setSubEmail('');
      setSubCount((c) => c + 1);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Subscription failed');
    } finally {
      setSubscribing(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton h-24 rounded-xl"></div>
          ))}
        </div>
        <div className="skeleton h-40 rounded-xl"></div>
        <div className="skeleton h-64 rounded-xl"></div>
      </div>
    );
  }

  const stats = [
    { label: 'Total Clients', value: dashboard?.totalClients || 0, icon: Users, color: 'text-gray-900', bg: 'bg-gray-50' },
    { label: 'Active Projects', value: dashboard?.activeProjects || 0, icon: FolderOpen, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Hours This Week', value: (dashboard?.hoursThisWeek || 0).toFixed(1), icon: Clock, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Total Earnings', value: `$${(dashboard?.totalEarnings || 0).toLocaleString()}`, icon: DollarSign, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Active Timers', value: dashboard?.activeTimer ? 1 : 0, icon: Timer, color: 'text-blue-600', bg: 'bg-blue-50', pulse: !!dashboard?.activeTimer },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-500">{stat.label}</span>
              <div className={`w-9 h-9 rounded-lg ${stat.bg} flex items-center justify-center`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
            </div>
            <div className={`text-2xl font-bold ${stat.label === 'Total Earnings' ? 'text-green-600' : 'text-gray-900'} flex items-center gap-2`}>
              {stat.value}
              {stat.pulse && <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse"></span>}
            </div>
          </div>
        ))}
      </div>

      {/* Active Timer */}
      {dashboard?.activeTimer && (
        <div className="bg-white rounded-xl border border-blue-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Timer className="w-5 h-5 text-blue-600 animate-pulse" />
                <h2 className="text-lg font-semibold text-gray-900">Timer Running</h2>
              </div>
              <p className="text-gray-500 text-sm">
                {dashboard.activeTimer.projectName || 'Project'} — {dashboard.activeTimer.description || 'No description'}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-3xl font-mono font-bold text-blue-600">{formatTime(elapsed)}</span>
              <button
                onClick={handleStop}
                disabled={stopping}
                className="flex items-center gap-2 bg-red-600 text-white px-4 py-2.5 rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                <Square className="w-4 h-4" />
                {stopping ? 'Stopping...' : 'Stop'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quick Start Timer */}
      {!dashboard?.activeTimer && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Start Timer</h2>
          <div className="flex flex-col sm:flex-row gap-3">
            <select
              value={timerProject}
              onChange={(e) => setTimerProject(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              <option value="">Select a project...</option>
              {projects.map((p) => (
                <option key={p._id || p.id} value={p._id || p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={timerDesc}
              onChange={(e) => setTimerDesc(e.target.value)}
              placeholder="What are you working on?"
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <button
              onClick={handleStart}
              disabled={starting}
              className="flex items-center gap-2 bg-green-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {starting ? 'Starting...' : 'Start'}
            </button>
          </div>
        </div>
      )}

      {/* Recent Time Logs */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Time Logs</h2>
        </div>
        {dashboard?.recentLogs && dashboard.recentLogs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Project</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Hours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {dashboard.recentLogs.map((log, i) => (
                  <tr key={log._id || log.id || i} className="hover:bg-gray-50">
                    <td className="px-6 py-3 text-sm text-gray-600">
                      {new Date(log.date || log.startTime).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3 text-sm font-medium text-gray-900">{log.projectName || '—'}</td>
                    <td className="px-6 py-3 text-sm text-gray-600">{log.description || '—'}</td>
                    <td className="px-6 py-3 text-sm text-gray-900 text-right font-medium">
                      {(log.hours || log.duration || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center text-gray-400 text-sm">No recent time logs</div>
        )}
      </div>

      {/* Subscribe */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-2">
          <Bell className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Stay Updated</h2>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Get notified about new features and updates. {subCount > 0 && <span className="text-blue-600 font-medium">{subCount} subscribers</span>}
        </p>
        <form onSubmit={handleSubscribe} className="flex gap-3">
          <input
            type="email"
            value={subEmail}
            onChange={(e) => setSubEmail(e.target.value)}
            placeholder="Enter your email"
            required
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <button
            type="submit"
            disabled={subscribing}
            className="bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 text-sm"
          >
            {subscribing ? 'Subscribing...' : 'Subscribe'}
          </button>
        </form>
      </div>
    </div>
  );
}
