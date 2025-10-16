// src/components/ResearchNotes.jsx
import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Download, FileText, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/lib/supabaseClient';

const POLL_INTERVAL_MS = 60000; // optional: 60s

const ResearchNotes = () => {
  const { toast } = useToast();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Adjust columns according to your DB schema
      const { data, error: fetchError } = await supabase
        .from('research_reports')
        .select('id, title, date, description, file_url, created_at')
        .order('created_at', { ascending: false });

      if (fetchError) throw fetchError;
      setReports(data ?? []);
    } catch (e) {
      console.error('Failed to fetch research notes', e);
      setError(e?.message || String(e));
      toast({
        title: 'Error loading reports',
        description: e?.message || 'See console for details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchReports();

    const id = setInterval(() => {
      fetchReports();
    }, POLL_INTERVAL_MS);

    return () => clearInterval(id);
  }, [fetchReports]);

  const handleDownload = (report) => {
    if (!report?.file_url) {
      toast({
        title: "File unavailable",
        description: "This report does not have a downloadable file.",
        duration: 3000,
      });
      return;
    }
    // open in new tab (works for public URLs). For protected files, call your server endpoint to stream.
    window.open(report.file_url, '_blank', 'noopener,noreferrer');
    toast({ title: 'Download started', description: report.title });
  };

  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-6">
          <h1 className="text-4xl sm:text-5xl font-bold text-foreground mb-3">In-Depth Research</h1>
          <p className="text-lg text-foreground/70 max-w-3xl mx-auto">
            Download our latest deep-dive reports and investment notes.
          </p>
        </motion.div>

        <div className="mb-6 flex items-center justify-end gap-3">
          <Button
            onClick={() => {
              fetchReports();
              toast({ title: 'Refreshing', description: 'Fetching latest reports...' });
            }}
            className="inline-flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="space-y-4 max-w-4xl mx-auto">
            {[1, 2, 3].map((n) => (
              <div key={n} className="animate-pulse bg-card border border-border rounded-lg p-6 flex items-center gap-6">
                <div className="bg-primary/10 p-4 rounded-lg h-12 w-12" />
                <div className="flex-1">
                  <div className="h-4 w-1/3 bg-gray-200 rounded mb-2" />
                  <div className="h-3 w-2/3 bg-gray-200 rounded mb-2" />
                  <div className="h-3 w-1/4 bg-gray-200 rounded" />
                </div>
                <div className="w-24 h-10 bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded p-4 text-sm text-red-700 mb-6">
            Error loading research notes: {error}
          </div>
        )}

        {/* Empty */}
        {!loading && reports.length === 0 && !error && (
          <div className="bg-card border border-border rounded-lg p-6 text-center text-muted-foreground">
            No research notes available yet. Add reports via your admin panel or through Supabase.
          </div>
        )}

        {/* Reports */}
        <div className="space-y-8 max-w-4xl mx-auto">
          {reports.map((report, index) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
              className="bg-card border border-border rounded-lg p-6 flex flex-col sm:flex-row items-start gap-6 hover:shadow-md transition-shadow"
            >
              <div className="bg-primary/10 p-4 rounded-lg">
                <FileText className="h-8 w-8 text-primary" />
              </div>

              <div className="flex-1">
                <p className="text-sm text-muted-foreground mb-1">
                  {report.date ? new Date(report.date).toLocaleDateString() : report.created_at ? new Date(report.created_at).toLocaleDateString() : '—'}
                </p>
                <h2 className="text-2xl font-bold text-card-foreground mb-2">{report.title ?? 'Untitled'}</h2>
                <p className="text-muted-foreground mb-4">{report.description ?? ''}</p>
              </div>

              <div className="flex-shrink-0 self-stretch flex items-center">
                <Button onClick={() => handleDownload(report)} className="w-full sm:w-auto">
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ResearchNotes;
