import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, DollarSign } from 'lucide-react';
import toast from 'react-hot-toast';
import * as api from '../api.js';

const statusColors = {
  draft: 'bg-gray-100 text-gray-600',
  sent: 'bg-blue-100 text-blue-700',
  paid: 'bg-green-100 text-green-700',
  overdue: 'bg-red-100 text-red-700',
};

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.getInvoices();
        setInvoices(res.data.invoices || res.data || []);
      } catch {
        toast.error('Failed to load invoices');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-10 w-48 rounded-lg"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-40 rounded-xl"></div>)}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
      </div>

      {invoices.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No invoices yet. Generate one from a project's time logs.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {invoices.map((invoice) => (
            <Link
              key={invoice._id || invoice.id}
              to={`/invoices/${invoice._id || invoice.id}`}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow block"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900">{invoice.invoiceNumber || `INV-${(invoice._id || invoice.id || '').slice(-6)}`}</h3>
                  <p className="text-sm text-gray-500 mt-0.5">{invoice.clientName || 'Client'}</p>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${statusColors[invoice.status] || statusColors.draft}`}>
                  {invoice.status || 'draft'}
                </span>
              </div>
              <p className="text-sm text-gray-500 mb-1">{invoice.projectName || 'Project'}</p>
              <p className="text-sm text-gray-400 mb-3">
                {new Date(invoice.date || invoice.createdAt).toLocaleDateString()}
              </p>
              <div className="pt-3 border-t border-gray-100 flex items-center gap-1.5">
                <DollarSign className="w-4 h-4 text-green-600" />
                <span className="text-lg font-bold text-green-600">${Number(invoice.total || invoice.totalAmount || 0).toFixed(2)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
