import React from 'react';
import { motion } from 'framer-motion';
import { Target, Users, Award, TrendingUp } from 'lucide-react';

const About = () => {
  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h1 className="text-4xl sm:text-5xl font-bold text-foreground mb-6">
            Our Mission
          </h1>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="aspect-video bg-muted rounded-lg overflow-hidden">
              <img 
                className="w-full h-full object-cover" 
                alt="Modern financial office with professionals analyzing data"
               src="https://images.unsplash.com/photo-1593630363221-fd977445c8e7" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col justify-center"
          >
            <p className="text-lg text-foreground/80 mb-6">
              Agarwal Global Investments is committed to delivering timely, actionable research and insights on global finance, economics, private equity and mergers & acquisitions. Our goal is to empower professionals and investors with high-quality, unbiased information.
            </p>
            <p className="text-lg text-foreground/80">
              With a commitment to analytical rigor and independent thinking, we cut through the noise to deliver insights that matter.
            </p>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"
        >
          {[
            {
              icon: Target,
              title: 'Strategic Focus',
              description: 'Deep expertise in finance, economics, and investment strategies'
            },
            {
              icon: Users,
              title: 'Expert Team',
              description: 'Seasoned analysts with decades of combined experience'
            },
            {
              icon: Award,
              title: 'Quality Research',
              description: 'Rigorous methodology and independent analysis'
            },
            {
              icon: TrendingUp,
              title: 'Global Perspective',
              description: 'Coverage of markets and trends worldwide'
            },
          ].map((item, index) => (
            <div
              key={index}
              className="bg-card p-6 rounded-lg border border-border hover:shadow-md transition-shadow"
            >
              <item.icon className="h-12 w-12 text-primary mb-4" />
              <h3 className="text-xl font-bold text-card-foreground mb-2">{item.title}</h3>
              <p className="text-muted-foreground">{item.description}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default About;