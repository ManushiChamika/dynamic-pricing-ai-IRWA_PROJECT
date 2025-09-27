import React, { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import gamingImg from "../../assets/gamingb.jpg";
import budgetImg from "../../assets/budgetb.jpg";

const preBuilds = [
  {
    id: 1,
    name: "Gaming Builds",
    image: gamingImg,
    description: "Ultimate performance for serious gamers. Perfect for 1440p/4K gaming.",
    link: "/gaming-builds",
    modernSuitability: "😈 Best for 2025 high-end gaming",
    performance: "🔥 High-performance graphics and processing",
    price: "LKR 1,000,000 - LKR 180,000",
    comparisonDescription: "Dominates AAA titles at max settings 1440p/4K",
    cpu: "Upto AMD Ryzen 7 7800X3D",
    gpu: "Upto NVIDIA RTX 4080 16GB",
    ram: "Upto 64GB DDR5 6000MHz",
    storage: "Upto 2TB NVMe SSD",
    gamingPerformance: "Upto 1440p @ 144+ FPS | 4K @ 90+ FPS",
    upgradePotential: "PCIe 5.0 ready, 1000W PSU for future GPUs",
    pros: ["4K gaming ready", "Excellent ray tracing", "Future-proof specs", "High overclocking potential", "Perfect for streaming"],
    cons: ["Higher power consumption", "Premium price tag", "Requires good cooling Solution", "Limited availability"],
    rating: 4.8,
    energyEfficiency: "Upto 850W PSU (80+ Gold)",
    warranty: "Upto 3 years parts + labor",
    aesthetics: "Tempered glass RGB case",
    priceToPerformance: 80,
    purchaseLink: "/gaming-builds"
  },
  {
    id: 2,
    name: "Budget Builds",
    image: budgetImg,
    description: "Great for esports and productivity. Balanced Performance.",
    link: "/budget-builds",
    modernSuitability: "✅ Perfect for everyday tasks",
    performance: "⚡ Smooth esports performance",
    price: "LKR 120,000 - LKR 16,000",
    comparisonDescription: "Excellent 1080p value with upgrade potential",
    cpu: "Upto Intel Core i5-13400F",
    gpu: "Upto AMD Radeon RX 7600 8GB",
    ram: "Upto 16GB DDR4 3200MHz",
    storage: "Upto 1TB NVMe SSD",
    gamingPerformance: "Upto 1080p @ 100+ FPS | 1440p @ 60+ FPS",
    upgradePotential: "2 RAM slots free, 650W PSU headroom",
    pros: ["Great value", "Energy efficient", "Easy to upgrade", "Compact design", "Good for everyday tasks"],
    cons: ["Limited/No ray tracing", "No 4K capability", "Less future-proof", "Less gaming performance"],
    rating: 4.5,
    energyEfficiency: "Upto 550W PSU (80+ Bronze)",
    warranty: "Upto 2 years parts only",
    aesthetics: "Minimalist micro-ATX case",
    priceToPerformance: 91,
    purchaseLink: "/budget-builds",    
  },
];

const BuildCard = React.memo(({ build, isSelected, onCompare }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <motion.div
      whileHover={{ 
        scale: 1.02,
        boxShadow: "0 10px 25px -5px rgba(0, 102, 255, 0.2), 0 8px 10px -6px rgba(0, 102, 255, 0.1)" 
      }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="bg-gradient-to-br from-gray-900 to-gray-800 p-6 rounded-xl border border-sky-500/30 relative overflow-hidden neon-box"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Tech Circuit Pattern Overlay */}
      <div className="absolute inset-0 opacity-20 z-0 bg-[radial-gradient(#3498db_1px,transparent_1px)] bg-[length:16px_16px]"></div>
      
      {/* Glass Reflection Effect */}
      <div className="absolute -inset-full h-56 w-56 z-0 opacity-30 bg-gradient-to-r from-cyan-400 to-sky-500 blur-sm transform rotate-12 -translate-y-16 animate-pulse"></div>
      
      <Link to={build.link} aria-label={`View ${build.name}`} className="block relative z-10">
        <div className="relative">
          <motion.img
            src={build.image}
            alt={build.name}
            className="w-full h-82 object-cover rounded-lg mb-5 transition-transform duration-300"
            loading="lazy"
            style={{
              clipPath: "polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%)"
            }}
            animate={{ filter: isHovered ? "brightness(1.4)" : "brightness(1)" }}
            transition={{ duration: 0.3 }}
          />
          
          {/* Glowing Border Effect */}
          <div className={`absolute inset-0 rounded-lg border-2 border-cyan-500 opacity-0 transition-opacity duration-300 ${isHovered ? 'opacity-60' : ''}`} 
               style={{
                 boxShadow: "0 0 15px 2px #0ea5e9",
                 clipPath: "polygon(0 0, 100% 0, 100% 85%, 95% 100%, 0 100%)"
               }}>
          </div>
          
          {/* Spec Highlight Badge */}
          <div className="absolute top-4 right-4 bg-cyan-600/90 text-white text-xs px-3 py-1 rounded-full backdrop-blur-sm neon-text">
            {build.id === 1 ? "ULTIMATE GAMING RIGS" : "RETRO BEASTS"}
          </div>
        </div>
      </Link>

      <div className="text-center relative z-10">
        <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-sky-500 mb-4 neon-text">
          {build.name}
        </h2>
        <p className="text-lg text-gray-200 mb-5">{build.description}</p>
        <div className="inline-block px-4 py-2 bg-gradient-to-r from-cyan-900/40 to-blue-900/40 rounded-lg backdrop-blur-sm border border-cyan-500/30 mb-3 neon-box">
          <p className="font-medium text-cyan-300">
            {build.modernSuitability}
          </p>
        </div>
        
        {/* Price Tag */}
        <div className="w-full py-2 px-3 bg-gradient-to-r from-gray-800/80 to-gray-900/80 backdrop-blur rounded-lg border border-gray-700 mb-5 neon-box">
          <p className="text-cyan-400 font-mono text-lg">{build.price}</p>
        </div>
      </div>

      <button
        onClick={() => onCompare(build)}
        className={`w-full mb-2 mt-5 py-3 rounded-lg transition-all duration-300 font-bold relative overflow-hidden group z-10 ${
          isSelected 
            ? "bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600" 
            : "bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700"
        } text-white neon-box`}
      >
        {/* Button Glow Effect */}
        <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-all duration-700"></span>
        <span className="relative z-10 flex items-center justify-center">
          {isSelected ? "Remove From Comparison" : "Compare Build"}
          <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ml-2 ${isSelected ? "rotate-45" : ""} transition-transform`} 
            fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {isSelected ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            )}
          </svg>
        </span>
      </button>
    </motion.div>
  );
});

const SpecBar = ({ label, value, maxValue, color }) => (
  <div className="mb-4">
    <div className="flex justify-between mb-1">
      <span className="font-mono text-lg text-cyan-300 neon-text">{label}</span>
      <span className="font-mono text-lg text-cyan-100 neon-text">{value}</span>
    </div>
    <div className="w-full bg-gray-700 rounded-full h-3 relative overflow-hidden neon-box">
      <div 
        className={`h-3 rounded-full ${color}`} 
        style={{ width: `${(parseInt(value) / maxValue) * 100}%` }}
      >
        <div className="absolute inset-0 opacity-30 animate-pulse bg-gradient-to-r from-transparent via-white to-transparent"></div>
      </div>
    </div>
  </div>
);

const ComparisonCard = ({ build }) => {
  const cpuScore = build.id === 1 ? 85 : 68;
  const gpuScore = build.id === 1 ? 90 : 65;
  const ramScore = build.id === 1 ? 97 : 60;
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="p-5 border border-cyan-500/30 rounded-lg bg-gradient-to-b from-gray-900 to-gray-800 backdrop-blur-sm relative overflow-hidden neon-box"
    >
      {/* Tech Circuit Pattern */}
      <div className="absolute inset-0 opacity-20 z-0 bg-[radial-gradient(#3498db_1px,transparent_1px)] bg-[length:12px_12px]"></div>
      
      {/* Decorative Tech Lines */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-blue-500"></div>
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-cyan-500 to-transparent"></div>
      
      <div className="relative z-10">
        <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-sky-500 text-center mb-6 neon-text">
          {build.name}
        </h2>
        
        <div className="space-y-7 text-gray-200 font-bold text-xl">
          {/* Performance Visualizations */}
          <div className="bg-gray-800/70 rounded-lg p-4 border border-gray-700 neon-box">
            <h3 className="font-semibold text-cyan-300 mb-4 neon-text">Performance Metrics</h3>
            <SpecBar label="CPU Power" value={cpuScore} maxValue={100} color="bg-gradient-to-r from-blue-500 to-cyan-400" />
            <SpecBar label="GPU Performance" value={gpuScore} maxValue={100} color="bg-gradient-to-r from-green-500 to-emerald-400" />
            <SpecBar label="Memory Speed" value={ramScore} maxValue={100} color="bg-gradient-to-r from-purple-500 to-fuchsia-400" />
          </div>
          
          {/* Core Specs */}
          <div className="bg-gray-800/70 rounded-lg p-4 border border-gray-700 neon-box">
            <h3 className="text-xl text-cyan-300 mb-5 neon-text">Core Components</h3>
            
            <div className="space-y-3">
              {/* CPU */}
              <div className="flex items-center">
                <div className="w-11 h-11 bg-blue-900/50 rounded-full flex items-center justify-center mr-3 border border-blue-500/30 neon-box">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg text-gray-400">CPU</p>
                  <p className="text-lg font-mono">{build.cpu}</p>
                </div>
              </div>
              
              {/* GPU */}
              <div className="flex items-center">
                <div className="w-11 h-11 bg-green-900/50 rounded-full flex items-center justify-center mr-3 border border-green-500/30 neon-box">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V5zm11 1h-1a1 1 0 00-1 1v3a1 1 0 001 1h1a1 1 0 001-1V7a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg text-gray-400">GPU</p>
                  <p className="text-lg font-mono">{build.gpu}</p>
                </div>
              </div>
              
              {/* RAM */}
              <div className="flex items-center">
                <div className="w-11 h-11 bg-purple-900/50 rounded-full flex items-center justify-center mr-3 border border-purple-500/30 neon-box">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-purple-400" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg text-gray-400">RAM</p>
                  <p className="text-lg font-mono">{build.ram}</p>
                </div>
              </div>
              
              {/* Storage */}
              <div className="flex items-center">
                <div className="w-11 h-11 bg-amber-900/50 rounded-full flex items-center justify-center mr-3 border border-amber-500/30 neon-box">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                    <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg text-gray-400">Storage</p>
                  <p className="text-lg font-mono">{build.storage}</p>
                </div>
              </div>

              {/* PSU */}
                  <div className="flex items-center">
                <div className="w-11 h-11 bg-red-900/50 rounded-full flex items-center justify-center mr-3 border border-red-500/30 neon-box">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg text-gray-400">Energy Efficiency</p>
                  <p className="text-lg font-mono">{build.energyEfficiency}</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Performance Stats */}
          <div className="bg-gray-800/70 rounded-lg p-4 border border-gray-700 neon-box">
            <h3 className="font-semibold text-cyan-300 mb-3 neon-text">Gaming Performance</h3>
            <div className="font-mono text-lg text-cyan-100 bg-gray-900/80 p-3 rounded border border-cyan-900/50 neon-box">
              {build.gamingPerformance}
            </div>
          </div>
          
          {/* Pros & Cons */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-emerald-900/20 rounded-lg p-3 border border-emerald-500/30 neon-box">
              <h3 className="text-lg font-semibold text-emerald-400 mb-3 flex items-center neon-text">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Pros
              </h3>
              <ul className="space-y-2">
                {build.pros.map((pro, i) => (
                  <li key={i} className="text-sm text-emerald-200 flex items-start neon-text">
                    <span className="text-emerald-400 mr-2">+</span> {pro}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="bg-rose-900/20 rounded-lg p-3 border border-rose-500/30 neon-box">
              <h3 className="text-lg font-semibold text-rose-400 mb-3 flex items-center neon-text">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"/>
                </svg>
                Things to Consider
              </h3>
              <ul className="space-y-2">
                {build.cons.map((con, i) => (
                  <li key={i} className="text-sm text-rose-200 flex items-start neon-text">
                    <span className="text-rose-400 mr-2">-</span> {con}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          
          {/* Price to Performance Gauge */}
          <div className="bg-gray-800/70 rounded-lg p-4 border border-gray-700 neon-box">
            <div className="flex justify-between mb-3">
              <h3 className="text-lg font-semibold text-cyan-300 neon-text">Price-to-Performance</h3>
              <span className="text-lg font-mono text-cyan-100 neon-text">{build.priceToPerformance}%</span>
            </div>
            <div className="w-full h-4 bg-gray-700 rounded-full overflow-hidden neon-box">
              <div
                className="h-full rounded-full relative bg-gradient-to-r from-cyan-500 to-blue-500"
                style={{ width: `${build.priceToPerformance}%` }}
              >
                <div className="absolute inset-0 opacity-30 animate-pulse bg-gradient-to-r from-transparent via-white to-transparent"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const CustomPreBuildList = ({ selectedBuilds, setSelectedBuilds }) => {
  const handleCompare = useCallback((build) => {
    setSelectedBuilds(prev => 
      prev.some(b => b.id === build.id) 
        ? prev.filter(b => b.id !== build.id)
        : prev.length < 2 ? [...prev, build] : prev
    );
  }, [setSelectedBuilds]);

  return (
    <div className="container mx-auto px-2 py-10 relative">
      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-[radial-gradient(#3498db_1px,transparent_1px)] bg-[length:20px_20px] opacity-5 pointer-events-none"></div>
          

      {/* Build Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {preBuilds.map(build => (
          <BuildCard
            key={build.id}
            build={build}
            isSelected={selectedBuilds.some(b => b.id === build.id)}
            onCompare={handleCompare}
          />
        ))}
      </div>

      {/* Comparison Section */}
      {selectedBuilds.length === 2 && (
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-16 relative"
        >
          <div className="absolute inset-0 -z-10 bg-gradient-to-b from-cyan-900/20 to-blue-900/20 rounded-2xl blur-xl"></div>
          
          <div className="bg-gradient-to-b from-gray-900 to-gray-800 rounded-xl shadow-2xl p-6 border border-sky-500/20 relative overflow-hidden neon-box">
            {/* Animated Corner Accent */}
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-gradient-to-br from-cyan-500/20 to-blue-500/10 rounded-full blur-xl"></div>
            
            <div className="flex items-center justify-center mb-8">
              <div className="h-px w-16 bg-gradient-to-r from-transparent to-cyan-500/50"></div>
              <h2 className="text-4xl font-extrabold text-center text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-400 px-4 neon-text">
                Battle Station Comparison
              </h2>
              <div className="h-px w-16 bg-gradient-to-l from-transparent to-cyan-500/50"></div>
            </div>
            
            {/* Comparison Cards */}
            <div className="grid md:grid-cols-2 gap-8">
              {selectedBuilds.map(build => (
                <ComparisonCard key={build.id} build={build} />
              ))}
            </div>

            {/* CTAs */}
            <div className="mt-8 grid grid-cols-2 gap-4">
              {selectedBuilds.map(build => (
                <div key={build.id} className="space-y-3">
                  <motion.a
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    href={build.purchaseLink}
                    className="block w-full py-3 text-center bg-gradient-to-r from-cyan-600 to-blue-700 hover:from-cyan-500 hover:to-blue-600 text-white rounded-lg transition-all relative overflow-hidden group neon-box"
                  >
                    {/* Button Glow Effect */}
                    <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-all duration-700"></span>
                    <span className="relative flex items-center justify-center">
                      Buy {build.name}
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </span>
                  </motion.a>                
                </div>
              ))}
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedBuilds([])}
              className="mt-6 w-full py-3 bg-gradient-to-r from-gray-700 to-gray-600 hover:from-rose-600 hover:to-red-600 text-white rounded-lg transition-all relative overflow-hidden group neon-box"
            >
              {/* Button Glow Effect */}
              <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-all duration-700"></span>
              <span className="relative flex items-center justify-center">
                Reset Comparison
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </span>
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default React.memo(CustomPreBuildList);