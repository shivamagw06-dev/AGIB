import React from 'react';
import { Linkedin, Twitter, Mail } from 'lucide-react';

const Footer = ({ setCurrentPage }) => {
  const handleNavClick = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCategoryClick = (category) => {
    setCurrentPage('live-articles');
    // In a real app, you'd pass the category to the ArticlesFeed component
    // For now, it just navigates to the page.
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-foreground text-background/70 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-2xl font-bold text-white mb-4 cursor-pointer" onClick={() => handleNavClick('home')}>
              Agarwal Global Investments
            </h3>
            <p className="text-background/60 mb-4 max-w-md">
              Delivering world-class research and analysis to empower informed investment decisions across global markets.
            </p>
            <div className="flex gap-4">
              <a href="#" className="bg-white/10 p-2 rounded-lg hover:bg-white/20 transition-colors">
                <Linkedin className="h-5 w-5" />
              </a>
              <a href="#" className="bg-white/10 p-2 rounded-lg hover:bg-white/20 transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="bg-white/10 p-2 rounded-lg hover:bg-white/20 transition-colors">
                <Mail className="h-5 w-5" />
              </a>
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li><button onClick={() => handleNavClick('home')} className="hover:text-white transition-colors">Home</button></li>
              <li><button onClick={() => handleNavClick('live-articles')} className="hover:text-white transition-colors">Live Articles</button></li>
              <li><button onClick={() => handleNavClick('about')} className="hover:text-white transition-colors">About Us</button></li>
              <li><button onClick={() => handleNavClick('contact')} className="hover:text-white transition-colors">Contact</button></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Categories</h4>
            <ul className="space-y-2">
              <li><button onClick={() => handleCategoryClick('Finance')} className="hover:text-white transition-colors">Finance</button></li>
              <li><button onClick={() => handleCategoryClick('Economics')} className="hover:text-white transition-colors">Economics</button></li>
              <li><button onClick={() => handleCategoryClick('Private Equity')} className="hover:text-white transition-colors">Private Equity</button></li>
              <li><button onClick={() => handleCategoryClick('M&A')} className="hover:text-white transition-colors">M&A</button></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/20 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-background/60 text-sm">
              © 2025 Agarwal Global Investments. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm">
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="hover:text-white transition-colors">Disclaimer</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;