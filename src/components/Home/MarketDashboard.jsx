import React from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Globe2,
  CalendarDays,
  Newspaper,
  ArrowUpRight,
} from "lucide-react";

const dashboard = [
  {
    title: "Market Sentiment",
    value: "Bullish",
    subtitle: "Positive momentum across banking & capital goods",
    icon: TrendingUp,
    color: "text-green-400",
  },
  {
    title: "Global Markets",
    value: "Mixed",
    subtitle: "US positive • Europe mixed • Asia stable",
    icon: Globe2,
    color: "text-cyan-400",
  },
  {
    title: "Economic Events",
    value: "4",
    subtitle: "High-impact releases this week",
    icon: CalendarDays,
    color: "text-orange-400",
  },
  {
    title: "Research Published",
    value: "15",
    subtitle: "Reports released today",
    icon: Newspaper,
    color: "text-blue-400",
  },
];

export default function MarketDashboard() {
  return (
    <section className="bg-slate-950 py-24">

      <div className="max-w-7xl mx-auto px-6">

        <div className="mb-14">

          <span className="text-blue-400 uppercase tracking-widest text-sm font-semibold">
            Dashboard
          </span>

          <h2 className="text-5xl font-bold text-white mt-3">
            Market Dashboard
          </h2>

          <p className="mt-5 text-slate-400 text-lg max-w-3xl">
            A quick snapshot of today's markets,
            research activity and macroeconomic developments.
          </p>

        </div>

        <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-8">

          {dashboard.map((card, index) => {

            const Icon = card.icon;

            return (

              <motion.div
                key={card.title}
                initial={{ opacity:0, y:20 }}
                whileInView={{ opacity:1, y:0 }}
                viewport={{ once:true }}
                transition={{ delay:index*0.1 }}
                whileHover={{ y:-6 }}
                className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8"
              >

                <div className="flex justify-between items-center">

                  <div className="w-14 h-14 rounded-2xl bg-slate-900 flex items-center justify-center">

                    <Icon className={card.color} size={28}/>

                  </div>

                  <ArrowUpRight className="text-slate-500"/>

                </div>

                <h3 className="mt-8 text-slate-400">
                  {card.title}
                </h3>

                <div className="mt-3 text-5xl font-bold text-white">
                  {card.value}
                </div>

                <p className="mt-4 text-slate-400 leading-7">
                  {card.subtitle}
                </p>

              </motion.div>

            );

          })}

        </div>

      </div>

    </section>
  );
}