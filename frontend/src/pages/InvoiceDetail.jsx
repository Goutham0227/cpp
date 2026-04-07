import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import * as api from '../api.js';

export default function InvoiceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.getInvoice(id);
        setInvoice(res.data.invoice || res.data);
      } catch {
        toast.error('Failed to load invoice');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [id]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this invoice?')) return;
    setDeleting(true);
    try {
      await api.deleteInvoice(id);
      toast.success('Invoice deleted');
      navigate('/invoices');
    } catch {
      toast.error('Failed to delete invoice');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-64 rounded-lg"></div>
        <div className="skeleton h-96 rounded-xl"></div>
      </div>
    );
  }

  if (!invoice) {
    return <div className="text-center py-12 text-gray-500">Invoice not found</div>;
  }

  const lineItems = invoice.lineItems || invoice.items || [];
  const subtotal = Number(invoice.subtotal) || lineItems.reduce((sum, item) => sum + (Number(item.amount) || Number(item.hours || 0) * Number(item.rate || 0)), 0);
  const tax = Number(invoice.tax) || 0;
  const total = Number(invoice.total) || Number(invoice.totalAmount) || (subtotal + tax);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/invoices')} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{invoice.invoiceNumber || 'Invoice'}</h1>
        </div>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="flex items-center gap-2 bg-red-600 text-white px-4 py-2.5 rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 text-sm"
        >
          <Trash2 className="w-4 h-4" />
          {deleting ? 'Deleting...' : 'Delete'}
        </button>
      </div>

      {/* Invoice Card */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Invoice Header */}
        <div className="px-8 py-6 border-b border-gray-200">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase">Invoice Number</span>
              <p className="text-lg font-semibold text-gray-900">{invoice.invoiceNumber || '—'}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase">Date</span>
              <p className="text-lg font-semibold text-gray-900">
                {new Date(invoice.date || invoice.createdAt).toLocaleDateString()}
              </p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase">Due Date</span>
              <p className="text-lg font-semibold text-gray-900">
                {invoice.dueDate ? new Date(invoice.dueDate).toLocaleDateString() : '—'}
              </p>
            </div>
          </div>
        </div>

        {/* Client & Project Info */}
        <div className="px-8 py-6 border-b border-gray-200">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase">Client</span>
              <p className="text-base font-semibold text-gray-900 mt-1">{invoice.clientName || '—'}</p>
              {invoice.clientEmail && <p className="text-sm text-gray-500">{invoice.clientEmail}</p>}
              {invoice.clientAddress && <p className="text-sm text-gray-500">{invoice.clientAddress}</p>}
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase">Project</span>
              <p className="text-base font-semibold text-gray-900 mt-1">{invoice.projectName || '—'}</p>
              {invoice.hourlyRate && <p className="text-sm text-gray-500">${invoice.hourlyRate}/hr</p>}
            </div>
          </div>
        </div>

        {/* Line Items */}
        {lineItems.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-8 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Hours</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Rate</th>
                  <th className="px-8 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {lineItems.map((item, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-8 py-3 text-sm text-gray-600">
                      {item.date ? new Date(item.date).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-900">{item.description || '—'}</td>
                    <td className="px-6 py-3 text-sm text-gray-900 text-right">{Number(item.hours || 0).toFixed(2)}</td>
                    <td className="px-6 py-3 text-sm text-gray-900 text-right">${Number(item.rate || 0).toFixed(2)}</td>
                    <td className="px-8 py-3 text-sm font-medium text-gray-900 text-right">
                      ${(Number(item.amount) || Number(item.hours || 0) * Number(item.rate || 0)).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Totals */}
        <div className="px-8 py-6 border-t border-gray-200 bg-gray-50">
          <div className="max-w-xs ml-auto space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Subtotal</span>
              <span className="font-medium text-gray-900">${subtotal.toFixed(2)}</span>
            </div>
            {tax > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Tax</span>
                <span className="font-medium text-gray-900">${tax.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between pt-2 border-t border-gray-200">
              <span className="text-base font-semibold text-gray-900">Total</span>
              <span className="text-2xl font-bold text-green-600">${total.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
