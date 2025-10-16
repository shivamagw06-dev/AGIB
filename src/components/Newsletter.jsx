import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';

const Newsletter = () => {
  const [email, setEmail] = useState('');
  const { toast } = useToast();

  const handleSubmit = (e) => {
    e.preventDefault();
    toast({
      title: "Successfully Subscribed! 🎉",
      description: "You'll receive our latest insights and updates.",
      duration: 4000,
    });
    setEmail('');
  };

  return (
    <section id="newsletter" className="py-20 bg-gradient-to-br from-primary to-purple-800">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <div className="bg-white/10 backdrop-blur-sm p-3 rounded-full w-16 h-16 mx-auto mb-6 flex items-center justify-center">
            <Mail className="h-8 w-8 text-white" />
          </div>
          
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Stay Ahead of the Markets
          </h2>
          
          <p className="text-lg text-purple-200 mb-8 max-w-2xl mx-auto">
            Get our latest finance, private equity & M&A insights delivered straight to your inbox.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="flex-1 bg-white/95 border-0 text-foreground placeholder:text-muted-foreground"
            />
            <Button
              type="submit"
              className="bg-white text-primary hover:bg-gray-200 font-semibold"
              size="lg"
            >
              Join the Newsletter
            </Button>
          </form>

          <p className="text-sm text-purple-300 mt-4">
            Join 10,000+ professionals receiving our insights
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default Newsletter;