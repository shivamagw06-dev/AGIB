import { ChevronRight } from "lucide-react";

const items = [
  "Morning Brief",
  "Markets",
  "Economy",
  "RBI Policy",
  "Inflation",
  "GDP",
  "Corporate Earnings",
  "IPO Watch",
  "Private Equity",
  "M&A",
  "Global Markets",
  "Oil",
  "Gold",
  "Copper",
];

export default function ResearchTicker() {
  return (
    <section className="border-b border-slate-200 bg-white">
      <div className="max-w-7xl mx-auto flex items-center overflow-x-auto whitespace-nowrap px-6 py-3 scrollbar-hide">

        <span className="mr-5 font-semibold text-blue-700">
          Today's Research
        </span>

        {items.map((item) => (
          <div
            key={item}
            className="flex items-center text-sm text-slate-700"
          >
            <span className="px-3 hover:text-blue-700 cursor-pointer transition-colors">
              {item}
            </span>

            <ChevronRight className="h-3 w-3 text-slate-300" />
          </div>
        ))}
      </div>
    </section>
  );
}