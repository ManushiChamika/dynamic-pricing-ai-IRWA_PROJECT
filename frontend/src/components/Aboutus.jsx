import React from 'react';
import { motion } from 'framer-motion';

const AboutUs = () => {
  // Animation variants
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  };

  return (
    <div className="bg-gradient-to-b from-gray-900 to-gray-800 text-gray-300 py-16 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16 relative"
        >
          <div className="absolute -top-10 -left-10 w-32 h-32 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
          <div className="absolute -bottom-8 -right-8 w-32 h-32 bg-red-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute top-0 right-20 w-32 h-32 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
          
          <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-red-500 mb-4">
            About <span className="text-red-400">ALPHA</span> IT SOLUTIONS
          </h1>
          <p className="text-xl text-gray-400 font-light tracking-wide">Level Up Your IT Experience</p>
          <div className="mt-6 flex justify-center">
            <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-red-500 rounded-full"></div>
          </div>
        </motion.div>

        {/* Two Column Section */}
        <motion.div 
          variants={container}
          initial="hidden"
          animate="show"
          className="grid md:grid-cols-2 gap-10 mb-16"
        >
          {/* Our Story */}
          <motion.div 
            variants={item}
            className="bg-gray-800 rounded-xl shadow-2xl p-8 hover:shadow-blue-500/20 transition-all duration-300 border border-gray-700 hover:border-blue-500/30 relative overflow-hidden"
          >
            <div className="absolute -right-10 -top-10 w-28 h-28 bg-blue-900 rounded-full opacity-20"></div>
            <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600 mb-5">
              Our Origin Story
            </h2>
            <p className="text-gray-300 leading-relaxed">
              <span className="font-semibold text-red-400">ALPHA</span> IT SOLUTIONS emerged from the digital shadows in
              Kelaniya, Sri Lanka, driven by a passion for cutting-edge technology. We embarked on a quest to
              provide high-performance new and battle-tested refurbished computers, laptops, accessories, and
              elite IT services.
            </p>
            <div className="mt-6">
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-1.5 rounded-full" style={{width: '85%'}}></div>
              </div>
            </div>
          </motion.div>

          {/* Our Expertise */}
          <motion.div 
            variants={item}
            className="bg-gray-800 rounded-xl shadow-2xl p-8 hover:shadow-red-500/20 transition-all duration-300 border border-gray-700 hover:border-red-500/30 relative overflow-hidden"
          >
            <div className="absolute -left-10 -bottom-10 w-28 h-28 bg-red-900 rounded-full opacity-20"></div>
            <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-red-600 mb-5">
              Mastering the Digital Arena
            </h2>
            <p className="text-gray-300 leading-relaxed">
              We are renowned for our mastery in intricate chip-level repairs, crafting custom PC builds optimized
              for peak performance, and delivering comprehensive technical support worthy of champions. Our
              squad of skilled professionals is dedicated to providing exceptional service.
            </p>
            <div className="mt-6">
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div className="bg-gradient-to-r from-red-500 to-pink-600 h-1.5 rounded-full" style={{width: '90%'}}></div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Digital Transformation Section */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-8 mb-16 border border-gray-700 relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 to-red-900/10 pointer-events-none"></div>
          <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-red-500 mb-6 relative">
            Entering a New Dimension
          </h2>
          <p className="text-gray-300 leading-relaxed mb-6 relative">
            To further empower our users, we've forged this state-of-the-art web application, designed to
            redefine your interaction with <span className="font-semibold text-red-400">ALPHA</span> IT SOLUTIONS. Our
            platform grants you the power to:
          </p>
          <ul className="grid md:grid-cols-2 gap-6 text-gray-300 relative">
            {[
              "Navigate our product catalog with ease",
              "Execute orders online, swiftly and securely",
              "Schedule service appointments at your convenience",
              "Forge your ultimate custom PC build with our experts",
              "Track orders in real-time with precision",
              "Access 24/7 customer support champions"
            ].map((feature, index) => (
              <motion.li 
                key={index}
                whileHover={{ x: 5 }}
                className="flex items-start bg-gray-800/50 rounded-lg p-4 hover:bg-gray-700/50 transition-all duration-200"
              >
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                    <svg
                      className="h-5 w-5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                </div>
                <span className="ml-3">{feature}</span>
              </motion.li>
            ))}
          </ul>
          <p className="text-gray-300 leading-relaxed mt-8 relative">
            With real-time order tracking and dedicated customer support, we are committed to enhancing service
            efficiency and ensuring your victory in the digital realm.
          </p>
        </motion.div>

        {/* Three Column Section */}
        <motion.div 
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid md:grid-cols-3 gap-10 mb-10"
        >
          {/* Our Mission */}
          <motion.div 
            variants={item}
            className="bg-gray-800 rounded-xl shadow-lg p-8 hover:shadow-blue-500/10 transition-all duration-300 border border-gray-700 hover:border-blue-500/50 relative overflow-hidden group"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="flex items-center mb-6 relative">
              <div className="p-3 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 text-white mr-4 shadow-lg">
                <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">
                Our Quest
              </h2>
            </div>
            <p className="text-gray-300 leading-relaxed relative">
              To arm our clients with dependable, cost-effective IT solutions while upholding the highest
              standards of quality and unwavering customer support.
            </p>
            <div className="mt-6">
              <span className="inline-block px-3 py-1 text-xs font-semibold bg-blue-900/30 text-blue-400 rounded-full">
                #Reliability
              </span>
            </div>
          </motion.div>

          {/* Our Vision */}
          <motion.div 
            variants={item}
            className="bg-gray-800 rounded-xl shadow-lg p-8 hover:shadow-purple-500/10 transition-all duration-300 border border-gray-700 hover:border-purple-500/50 relative overflow-hidden group"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-900/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="flex items-center mb-6 relative">
              <div className="p-3 rounded-xl bg-gradient-to-br from-purple-600 to-purple-800 text-white mr-4 shadow-lg">
                <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-purple-600">
                Our Grand Design
              </h2>
            </div>
            <p className="text-gray-300 leading-relaxed relative">
              To ascend as Sri Lanka's foremost IT solutions provider through relentless innovation, superior
              service, and a player-centric approach.
            </p>
            <div className="mt-6">
              <span className="inline-block px-3 py-1 text-xs font-semibold bg-purple-900/30 text-purple-400 rounded-full">
                #Innovation
              </span>
            </div>
          </motion.div>

          {/* Our Values */}
          <motion.div 
            variants={item}
            className="bg-gray-800 rounded-xl shadow-lg p-8 hover:shadow-red-500/10 transition-all duration-300 border border-gray-700 hover:border-red-500/50 relative overflow-hidden group"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-red-900/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="flex items-center mb-6 relative">
              <div className="p-3 rounded-xl bg-gradient-to-br from-red-600 to-red-800 text-white mr-4 shadow-lg">
                <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-red-600">
                Our Core Principles
              </h2>
            </div>
            <ul className="space-y-3 text-gray-300 relative">
              {[
                "Unwavering Quality & Reliability",
                "Championing Customer Satisfaction",
                "Relentless Innovation & Excellence",
                "Absolute Integrity & Transparency",
                "Cutting-Edge Technical Mastery",
                "Community-Focused Solutions"
              ].map((value, index) => (
                <li key={index} className="flex items-start">
                  <div className="flex-shrink-0 mt-1">
                    <div className="h-4 w-4 rounded-full bg-gradient-to-r from-red-500 to-pink-500"></div>
                  </div>
                  <span className="ml-3">{value}</span>
                </li>
              ))}
            </ul>
            <div className="mt-6">
              <span className="inline-block px-3 py-1 text-xs font-semibold bg-red-900/30 text-red-400 rounded-full">
                #Excellence
              </span>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

export default AboutUs;