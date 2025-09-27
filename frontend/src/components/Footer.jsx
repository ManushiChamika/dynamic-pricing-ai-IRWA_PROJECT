import React from 'react';
import { Link } from 'react-router';
import { FaFacebook, FaTwitter, FaInstagram, FaLinkedin, FaYoutube } from 'react-icons/fa';

const Footer = () => {
  const footerLinks = {
    company: {
      title: 'Services',
      links: [
        { name: 'About Us', href: '/about' },
        { name: 'Services', href: '/appointment' },
        { name: 'Custom Pre-Builds', href: '/custom-prebuilds' },
        { name: 'Faq', href: '/faq' },
        { name: 'Contact Us', href: '/ContactUs' }
      ]
    },
    resources: {
      title: 'AI Services',
      links: [
        { name: 'Technova Support', href: '/ContactUs' },
        { name: 'Smart Product Categorization', href: '/AI-Engine' },
        { name: 'Build Compatibility Checker', href: '/AI-build-suggestor' },
        { name: 'AI Computer Diagnosticians', href: '/AppointmenentAI' },
        { name: 'Order & Finance Intelligence', href: '/OrderSupportChat' }
      ]
    }
  };

  const socialLinks = [
    { icon: <FaFacebook />, href: 'https://facebook.com' },
    { icon: <FaTwitter />, href: 'https://twitter.com' },
    { icon: <FaInstagram />, href: 'https://instagram.com' },
    { icon: <FaLinkedin />, href: 'https://linkedin.com' },
    { icon: <FaYoutube />, href: 'https://youtube.com' }
  ];

  return (
    <footer className="bg-black text-white pt-20 pb-10">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between md:gap-24 gap-16 mb-16">
          {/* Left side with logo and description */}
          <div className="md:w-1/3">
            <Link to="/" className="text-2xl font-bold mb-4 inline-block">
              <span className="text-blue-500">ALPHA IT SOLUTIONS</span> .
            </Link>
            <p className="text-gray-400 md:w-2/3">
            Get the latest IT products and expert services, all in one place. Fast, reliable, and built for your needs!
            </p>
          </div>

          {/* Right side with links grid */}
          <div className="md:w-2/3">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-8 items-center">
              {Object.values(footerLinks).map((section) => (
                <div key={section.title}>
                  <h3 className="text-lg font-semibold mb-4">{section.title}</h3>
                  <ul className="space-y-2">
                    {section.links.map((link) => (
                      <li key={link.name}>
                        <Link 
                          to={link.href}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          {link.name}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom section with social links and copyright */}
        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
          <div className="flex space-x-6 mb-4 md:mb-0">
            {socialLinks.map((social, index) => (
              <a
                key={index}
                href={social.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white transition-colors text-xl"
              >
                {social.icon}
              </a>
            ))}
          </div>
          <div className="text-gray-400 text-sm">
            © {new Date().getFullYear()} Alpha IT Solutions. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;