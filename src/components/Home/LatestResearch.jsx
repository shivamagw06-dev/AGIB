import React from "react";
import { motion } from "framer-motion";
import { Clock3, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const reports = [
  {
    category: "Macro",
    title: "RBI Monetary Policy Preview",
    summary:
      "Expectations ahead of the upcoming RBI MPC meeting and implications for markets.",
    read: "6 min",
    premium: false,
  },
  {
    category: "Equity Research",
    title: "Reliance Industries Q1 Analysis",
    summary:
      "Detailed earnings breakdown, segment performance and valuation outlook.",
    read: "12 min",
    premium: true,
  },
  {
    category: "Markets",
    title: "Global Markets Morning Brief",
    summary:
      "US, Europe, Asia and commodity market developments overnight.",
    read: "5 min",
    premium: false,
  },
  {
    category: "Private Markets",
    title: "India PE Weekly Roundup",
    summary:
      "Latest private equity transactions, funding rounds and exits.",
    read: "8 min",
    premium: true,
  },
  {
    category: "Economy",
    title: "India Inflation Tracker",
    summary:
      "CPI, WPI and inflation expectations with historical comparison.",
    read: "7 min",
    premium: false,
  },
  {
    category: "Sector Research",
    title: "Indian Banking Sector Update",
    summary:
      "Credit growth, NIMs, valuation and risk outlook for FY27.",
    read: "10 min",
    premium: true,
  },
];

export default function LatestResearch() {
  return (
    <section className="bg-slate-950 py-24">

      <div className="max-w-7xl mx-auto px-6">

        <div className="flex justify-between items-center mb-12">

          <div>

            <p className="text-blue-400 uppercase tracking-widest text-sm">
              Research Feed
            </p>

            <h2 className="text-5xl font-bold text-white mt-3">
              Latest Research
            </h2>

          </div>

          <Button variant="outline">
            View All
          </Button>

        </div>

        <div className="grid lg:grid-cols-2 gap-8">

          {reports.map((report, index) => (

            <motion.div
              key={report.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{
                delay: index * 0.1,
              }}
              whileHover={{
                y: -5,
              }}
              className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8"
            >

              <div className="flex justify-between items-center">

                <span className="text-blue-400 text-sm">
                  {report.category}
                </span>

                {report.premium && (

                  <span className="rounded-full bg-yellow-500/20 text-yellow-300 text-xs px-3 py-1">
                    Premium
                  </span>

                )}

              </div>

              <h3 className="mt-5 text-2xl font-semibold text-white">

                {report.title}

              </h3>

              <p className="mt-5 text-slate-400 leading-7">

                {report.summary}

              </p>

              <div className="flex justify-between items-center mt-8">

                <div className="flex items-center gap-2 text-slate-400">

                  <Clock3 size={16} />

                  {report.read}

                </div>

                <Button
                  variant="ghost"
                  className="text-blue-400"
                >
                  Read

                  <ArrowRight
                    className="ml-2"
                    size={16}
                  />
                </Button>

              </div>

            </motion.div>

          ))}

        </div>

      </div>

    </section>
  );
}