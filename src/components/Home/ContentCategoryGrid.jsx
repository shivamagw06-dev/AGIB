import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { HOME_CATEGORIES } from '@/config/contentCategories';

export default function ContentCategoryGrid() {
  const navigate = useNavigate();

  return (
    <section className="bg-slate-50 border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-6 py-16 md:py-20">
        <div className="text-center mb-12 md:mb-14">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            What would you like to read?
          </h2>
          <p className="mt-3 text-slate-600 max-w-xl mx-auto">
            Choose a section below — each opens dedicated market updates, research, or live data.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
          {HOME_CATEGORIES.map((category) => {
            const Icon = category.icon;
            return (
              <button
                key={category.id}
                type="button"
                onClick={() => navigate(category.path)}
                className="group text-left rounded-xl border border-slate-200 bg-white p-6 md:p-7 shadow-sm hover:shadow-md hover:border-slate-300 hover:-translate-y-0.5 transition-all duration-200"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 text-slate-700 group-hover:bg-blue-50 group-hover:text-blue-700 transition-colors">
                  <Icon size={22} strokeWidth={1.75} />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-slate-900 group-hover:text-blue-800 transition-colors">
                  {category.title}
                </h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                  {category.description}
                </p>
                <span className="mt-5 inline-flex items-center text-sm font-medium text-blue-700 opacity-0 group-hover:opacity-100 transition-opacity">
                  Open section
                  <ArrowRight className="ml-1.5 h-4 w-4" />
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
