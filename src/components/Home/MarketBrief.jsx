import React from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Globe2,
  CalendarDays,
  Newspaper,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const themes = [
  "RBI Policy Preview",
  "Banking Sector",
  "Oil Prices",
  "US Markets",
  "Inflation",
  "FII / DII Flows",
];

const events = [
  {
    title: "India CPI",
    date: "Tomorrow",
  },
  {
    title: "RBI MPC Meeting",
    date: "This Week",
  },
  {
    title: "US FOMC",
    date: "Next Week",
  },
];

export default function MarketBrief() {
  return (
    <section className="relative py-24 bg-slate-950">

      <div className="max-w-7xl mx-auto px-6">

        <motion.div
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16 text-center"
        >

          <span className="inline-flex rounded-full bg-blue-600/10 border border-blue-500/20 px-4 py-2 text-blue-300 text-sm font-medium">

            Daily Intelligence

          </span>

          <h2 className="mt-6 text-5xl font-bold text-white">

            Today's Market Intelligence

          </h2>

          <p className="mt-5 text-slate-400 text-lg max-w-3xl mx-auto">

            Institutional-quality market intelligence
            summarising the key developments every investor
            should know before making decisions.

          </p>

        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">

          {/* LEFT */}

          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8"
          >

            <div className="flex items-center gap-3">

              <TrendingUp className="text-green-400" />

              <h3 className="text-2xl font-bold text-white">
                Market Themes
              </h3>

            </div>

            <div className="mt-8 space-y-4">

              {themes.map((theme) => (

                <div
                  key={theme}
                  className="rounded-xl border border-white/10 bg-slate-900/70 p-4 text-slate-300 hover:border-blue-500 transition"
                >
                  {theme}
                </div>

              ))}

            </div>

          </motion.div>

          {/* MIDDLE */}

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8"
          >

            <div className="flex items-center gap-3">

              <Globe2 className="text-cyan-400" />

              <h3 className="text-2xl font-bold text-white">
                Global Markets
              </h3>

            </div>

            <div className="mt-8 space-y-5">

              {[
                "Asia Markets",
                "Europe Markets",
                "United States",
                "Commodities",
                "Currencies",
                "Bond Markets",
              ].map((item) => (

                <div
                  key={item}
                  className="flex justify-between border-b border-white/10 pb-4"
                >

                  <span className="text-slate-300">
                    {item}
                  </span>

                  <span className="text-blue-400">
                    Analysis →
                  </span>

                </div>

              ))}

            </div>

          </motion.div>

          {/* RIGHT */}

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8"
          >

            <div className="flex items-center gap-3">

              <CalendarDays className="text-orange-400" />

              <h3 className="text-2xl font-bold text-white">
                Economic Calendar
              </h3>

            </div>

            <div className="mt-8 space-y-5">

              {events.map((event) => (

                <div
                  key={event.title}
                  className="flex justify-between border-b border-white/10 pb-4"
                >

                  <div>

                    <p className="text-white">
                      {event.title}
                    </p>

                    <p className="text-slate-500 text-sm">
                      High Impact
                    </p>

                  </div>

                  <span className="text-blue-400">
                    {event.date}
                  </span>

                </div>

              ))}

            </div>

            <div className="mt-10">

              <Button className="w-full h-12 bg-blue-600 hover:bg-blue-700">

                <Newspaper className="mr-2 h-4 w-4" />

                Read Morning Report

                <ArrowRight className="ml-2 h-4 w-4" />

              </Button>

            </div>

          </motion.div>

        </div>

      </div>

    </section>
  );
}