import { ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export default function InstitutionalHero() {
  const navigate = useNavigate();

  return (
    <section className="bg-white border-b border-slate-200">
      <div className="max-w-5xl mx-auto px-6 py-20 md:py-28 text-center">
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-[3.25rem] font-bold text-slate-900 leading-tight tracking-tight">
          Institutional-Quality Market Research for Indian Investors
        </h1>
        <p className="mt-6 text-lg md:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
          Daily market updates, company research, earnings analysis, and actionable investment insights.
        </p>
        <div className="mt-10">
          <Button
            size="lg"
            onClick={() => navigate('/research')}
            className="h-12 px-8 text-base bg-blue-700 hover:bg-blue-800 rounded-md shadow-sm"
          >
            Explore Today&apos;s Research
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </section>
  );
}
