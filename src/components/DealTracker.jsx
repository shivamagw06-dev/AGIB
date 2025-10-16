// src/components/DealTracker.jsx
import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Building2, MapPin, RefreshCw } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/lib/supabaseClient';

const POLL_INTERVAL_MS = 30000; // 30s poll (optional)

const DealTracker = () => {
  const { toast } = useToast();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDeals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Adjust selected columns if your table has different columns
      const { data, error: fetchError } = await supabase
        .from('deals')
        .select('id, acquirer, target, value, sector, region, type, created_at')
        .order('created_at', { ascending: false });

      if (fetchError) throw fetchError;
      setDeals(data ?? []);
    } catch (e) {
      console.error('Failed to load deals', e);
      setError(e.message || String(e));
      toast({
        title: 'Failed to load deals',
        description: e?.message || 'Check console for details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchDeals();

    // Optional: polling to keep UI fresh
    const id = setInterval(() => {
      fetchDeals();
    }, POLL_INTERVAL_MS);

    return () => clearInterval(id);
  }, [fetchDeals]);

  // Optional: lightweight formatting helper
  const formatValue = (v) => (v ? v : '—');

  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-6">
          <h1 className="text-4xl sm:text-5xl font-bold text-foreground mb-3">Tracking the World of Deals</h1>
          <p className="text-lg text-foreground/70 max-w-3xl mx-auto">
            Live updates on private equity & M&amp;A activity across sectors and regions.
          </p>
        </motion.div>

        <div className="mb-6 flex items-center justify-end gap-3">
          <button
            onClick={() => {
              fetchDeals();
              toast({ title: 'Refreshing', description: 'Fetching latest deals...' });
            }}
            className="inline-flex items-center gap-2 px-3 py-1.5 border rounded shadow-sm hover:bg-gray-50"
            aria-label="Refresh deals"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Refresh</span>
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="space-y-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="animate-pulse bg-card border border-border rounded-lg p-6">
                <div className="h-6 w-3/4 bg-gray-200 rounded mb-3"></div>
                <div className="h-4 w-1/3 bg-gray-200 rounded mb-4"></div>
                <div className="h-3 w-1/5 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded p-4 text-sm text-red-700 mb-6">
            Error loading deals: {error}
          </div>
        )}

        {/* Empty */}
        {!loading && deals.length === 0 && !error && (
          <div className="bg-card border border-border rounded-lg p-6 text-center text-muted-foreground">
            No deals found yet. You can add deals in your admin panel or via Supabase.
          </div>
        )}

        {/* Deals list */}
        <div className="space-y-8">
          {deals.map((deal, index) => (
            <motion.div
              key={deal.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.06 }}
              className="bg-card border border-border rounded-lg p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4">
                <div>
                  <span
                    className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${
                      deal.type === 'M&A' ? 'bg-primary/10 text-primary' : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {deal.type ?? 'Deal'}
                  </span>
                  <h2 className="text-2xl font-bold text-card-foreground mt-2">{deal.target ?? '—'}</h2>
                  <p className="text-muted-foreground">acquired by {deal.acquirer ?? '—'}</p>
                </div>

                <div className="mt-4 sm:mt-0 text-3xl font-bold text-primary">
                  {formatValue(deal.value)}
                </div>
              </div>

              <div className="border-t border-border pt-4 mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  <span>{deal.sector ?? '—'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  <span>{deal.region ?? '—'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-gray-100">{new Date(deal.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default DealTracker;
