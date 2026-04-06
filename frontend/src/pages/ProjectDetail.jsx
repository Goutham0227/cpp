import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Square, Timer, Pencil, Trash2, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import * as api from '../api.js';

const statusColors = {
  active: 'bg-green-100 text-green-700',
  paused: 'bg-gray-100 text-gray-600',
  completed: 'bg-blue-100 text-blue-700',
};

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [timeLogs, setTimeLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timerDesc, setTimerDesc] = useState('');
  const [timerRunning, setTimerRunning] = useState(false);
  const [activeTimer, setActiveTimer] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', hourlyRate: '', status: '', description: '' });
  const [saving, setSaving] = useState(false);
  const [manualForm, setManualForm] = useState({ date: '', startTime: '', endTime: '', description: '', billable: true });
  const [addingManual, setAddingManual] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [editingLog, setEditingLog] = useState(null);
  const [editLogForm, setEditLogForm] = useState({});
  const intervalRef = useRef(null);

  const fetchData = async () => {
    try {
      const [projRes, logsRes] = await Promise.all([
        api.getProject(id),
        api.getTimeLogs(id),
      ]);
      const proj = projRes.data.project || projRes.data;
      setProject(proj);
      setTimeLogs(logsRes.data.timeLogs || logsRes.data || []);
      setEditForm({
        name: proj.name || '',
        hourlyRate: proj.hourlyRate || '',
        status: proj.status || 'active',
        description: proj.description || '',
      });
      if (proj.activeTimer) {
        setTimerRunning(true);
        setActiveTimer(proj.activeTimer);
      }
    } catch {
      toast.error('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [id]);

  useEffect(() => {
    if (activeTimer) {
      const startTime = new Date(activeTimer.startTime).getTime();
      const update = () => setElapsed(Math.floor((Date.now() - startTime) / 1000));
      update();
      intervalRef.current = setInterval(update, 1000);
      return () => clearInterval(intervalRef.current);
    } else {
      setElapsed(0);
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
  }, [activeTimer]);

  const formatTime = (s) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  };

  const handleStart = async () => {
    setStarting(true);
    try {
      const res = await api.startTimer({ projectId: id, description: timerDesc });
      setTimerRunning(true);
      setActiveTimer(res.data.timer || res.data);
      setTimerDesc('');
      toast.success('Timer started');
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to start timer');
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    if (!activeTimer) return;
    setStopping(true);
    try {
      await api.stopTimer(activeTimer._id || activeTimer.id);
      setTimerRunning(false);
      setActiveTimer(null);
      toast.success('Timer stopped');
      fetchData();
    } catch {
      toast.error('Failed to stop timer');
    } finally {
      setStopping(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateProject(id, { ...editForm, hourlyRate: parseFloat(editForm.hourlyRate) || 0 });
      toast.success('Project updated');
      setShowEdit(false);
      fetchData();
    } catch {
      toast.error('Failed to update project');
    } finally {
      setSaving(false);
    }
  };

  const handleManualEntry = async (e) => {
    e.preventDefault();
    setAddingManual(true);
    try {
      const payload = {
        description: manualForm.description,
        billable: manualForm.billable,
        startTime: `${manualForm.date}T${manualForm.startTime}:00Z`,
        endTime: `${manualForm.date}T${manualForm.endTime}:00Z`,
      };
      await api.createTimeLog(id, payload);
      toast.success('Time log added');
      setManualForm({ date: '', startTime: '', endTime: '', description: '', billable: true });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to add time log');
    } finally {
      setAddingManual(false);
    }
  };

  const handleDeleteLog = async (logId) => {
    if (!confirm('Delete this time log?')) return;
    try {
      await api.deleteTimeLog(id, logId);
      toast.success('Time log deleted');
      fetchData();
    } catch {
      toast.error('Failed to delete');
    }
  };

  const handleEditLog = (log) => {
    setEditingLog(log._id || log.id);
    setEditLogForm({
      description: log.description || '',
      hours: log.hours || log.duration || 0,
      billable: log.billable !== false,
    });
  };

  const handleSaveLog = async (logId) => {
    try {
      await api.updateTimeLog(id, logId, editLogForm);
      toast.success('Time log updated');
      setEditingLog(null);
      fetchData();
    } catch {
      toast.error('Failed to update');
    }
  };

  const handleGenerateInvoice = async () => {
    setGenerating(true);
    try {
      const res = await api.generateInvoice({ projectId: id });
      toast.success('Invoice generated!');
      navigate(`/invoices/${res.data.invoice?._id || res.data.invoice?.id || res.data._id || res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to generate invoice');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-64 rounded-lg"></div>
        <div className="skeleton h-32 rounded-xl"></div>
        <div className="skeleton h-48 rounded-xl"></div>
      </div>
    );
  }

  if (!project) {
    return <div className="text-center py-12 text-gray-500">Project not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/projects')} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-sm text-gray-500">{project.clientName || 'No client'}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${statusColors[project.status] || statusColors.active}`}>
          {project.status || 'active'}
        </span>
      </div>

      {/* Project Info */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <span className="text-xs text-gray-500 uppercase">Hourly Rate</span>
            <p className="text-lg font-semibold text-gray-900">${project.hourlyRate || 0}/hr</p>
          </div>
          <div>
            <span className="text-xs text-gray-500 uppercase">Total Hours</span>
            <p className="text-lg font-semibold text-gray-900">{(project.totalHours || 0).toFixed(1)}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500 uppercase">Total Earned</span>
            <p className="text-lg font-semibold text-green-600">${((project.totalHours || 0) * (project.hourlyRate || 0)).toFixed(2)}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500 uppercase">Time Logs</span>
            <p className="text-lg font-semibold text-gray-900">{timeLogs.length}</p>
          </div>
        </div>
      </div>

      {/* Timer Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Timer</h2>
        {timerRunning ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Timer className="w-6 h-6 text-blue-600 animate-pulse" />
              <div>
                <span className="text-3xl font-mono font-bold text-blue-600">{formatTime(elapsed)}</span>
                <p className="text-sm text-gray-500 mt-1">{activeTimer?.description || 'No description'}</p>
              </div>
            </div>
            <button
              onClick={handleStop}
              disabled={stopping}
              className="flex items-center gap-2 bg-red-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              <Square className="w-4 h-4" />
              {stopping ? 'Stopping...' : 'Stop'}
            </button>
          </div>
        ) : (
          <div className="flex gap-3">
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
        )}
      </div>

      {/* Time Logs Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Time Logs</h2>
          <button
            onClick={handleGenerateInvoice}
            disabled={generating || timeLogs.length === 0}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            {generating ? 'Generating...' : 'Generate Invoice'}
          </button>
        </div>
        {timeLogs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Hours</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Billable</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {timeLogs.map((log) => {
                  const logId = log._id || log.id;
                  const isEditing = editingLog === logId;
                  return (
                    <tr key={logId} className="hover:bg-gray-50">
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {new Date(log.date || log.startTime).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-900">
                        {isEditing ? (
                          <input
                            type="text"
                            value={editLogForm.description}
                            onChange={(e) => setEditLogForm({ ...editLogForm, description: e.target.value })}
                            className="border border-gray-300 rounded px-2 py-1 text-sm w-full"
                          />
                        ) : (
                          log.description || '—'
                        )}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-900 text-right font-medium">
                        {isEditing ? (
                          <input
                            type="number"
                            step="0.01"
                            value={editLogForm.hours}
                            onChange={(e) => setEditLogForm({ ...editLogForm, hours: parseFloat(e.target.value) || 0 })}
                            className="border border-gray-300 rounded px-2 py-1 text-sm w-20 text-right"
                          />
                        ) : (
                          (log.hours || log.duration || 0).toFixed(2)
                        )}
                      </td>
                      <td className="px-6 py-3 text-center">
                        {isEditing ? (
                          <input
                            type="checkbox"
                            checked={editLogForm.billable}
                            onChange={(e) => setEditLogForm({ ...editLogForm, billable: e.target.checked })}
                            className="w-4 h-4 text-blue-600 rounded"
                          />
                        ) : (
                          <span className={`inline-block w-2.5 h-2.5 rounded-full ${log.billable !== false ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                        )}
                      </td>
                      <td className="px-6 py-3 text-right">
                        {isEditing ? (
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => handleSaveLog(logId)} className="text-xs text-blue-600 font-medium hover:text-blue-700">Save</button>
                            <button onClick={() => setEditingLog(null)} className="text-xs text-gray-500 font-medium hover:text-gray-700 ml-2">Cancel</button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => handleEditLog(log)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors">
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={() => handleDeleteLog(logId)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center text-gray-400 text-sm">No time logs yet. Start the timer or add a manual entry.</div>
        )}
      </div>

      {/* Manual Time Entry */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Manual Time Entry</h2>
        <form onSubmit={handleManualEntry} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Date</label>
            <input
              type="date"
              value={manualForm.date}
              onChange={(e) => setManualForm({ ...manualForm, date: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Start Time</label>
            <input
              type="time"
              value={manualForm.startTime}
              onChange={(e) => setManualForm({ ...manualForm, startTime: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">End Time</label>
            <input
              type="time"
              value={manualForm.endTime}
              onChange={(e) => setManualForm({ ...manualForm, endTime: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
            <input
              type="text"
              value={manualForm.description}
              onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
              placeholder="What did you work on?"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={manualForm.billable}
                onChange={(e) => setManualForm({ ...manualForm, billable: e.target.checked })}
                className="w-4 h-4 text-blue-600 rounded"
              />
              Billable
            </label>
            <button
              type="submit"
              disabled={addingManual}
              className="bg-blue-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 whitespace-nowrap"
            >
              {addingManual ? 'Adding...' : 'Add Entry'}
            </button>
          </div>
        </form>
      </div>

      {/* Edit Project (Collapsible) */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <button
          onClick={() => setShowEdit(!showEdit)}
          className="w-full flex items-center justify-between px-5 py-4 text-left"
        >
          <h2 className="text-lg font-semibold text-gray-900">Edit Project</h2>
          {showEdit ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </button>
        {showEdit && (
          <form onSubmit={handleUpdate} className="px-5 pb-5 space-y-4 border-t border-gray-200 pt-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hourly Rate ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={editForm.hourlyRate}
                  onChange={(e) => setEditForm({ ...editForm, hourlyRate: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                >
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button type="submit" disabled={saving} className="bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50">
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
