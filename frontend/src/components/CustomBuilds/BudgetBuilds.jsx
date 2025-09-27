import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useTheme } from "./ThemeContext";
import { FaSun, FaMoon, FaChevronUp } from "react-icons/fa";
import { motion } from "framer-motion";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend} from "recharts";
import { Cpu, Zap, AlertTriangle } from 'lucide-react';

// API URL for budget builds
const API_URL = "http://localhost:5000/api/prebuilds/category/Budget";

// Function to format price correctly
const formatPrice = (price) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "LKR",
  }).format(price);
};

const navigate = (path) => {
  console.log(`Navigating to: ${path}`);
};  


const BudgetBuilds = () => {
  const { isDark, toggleTheme } = useTheme();
  const [budgetBuilds, setBudgetBuilds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBuilds, setSelectedBuilds] = useState([]);
  const [productsLookup, setProductsLookup] = useState({});
  const [showScrollTop, setShowScrollTop] = useState(false);
  const navigate = useNavigate();
  const [hoverExplore, setHoverExplore] = useState(false);
  const [hoverAI, setHoverAI] = useState(false);
  const [glitchEffect, setGlitchEffect] = useState(false);
  const [glitchText, setGlitchText] = useState(false);
  
    useEffect(() => {
      let glitchInterval;
      let textInterval;
      
      if (hoverAI) {
        // More frequent glitches when hovering
        glitchInterval = setInterval(() => {
          setGlitchEffect(true);
          setTimeout(() => setGlitchEffect(false), 150);
        }, 800);
        
        // Text glitch effect
        textInterval = setInterval(() => {
          setGlitchText(true);
          setTimeout(() => setGlitchText(false), 100);
        }, 1200);
      }
      
      return () => {
        clearInterval(glitchInterval);
        clearInterval(textInterval);
      };
    }, [hoverAI]);
  
  // Fetching budget builds data from API
  useEffect(() => {
    axios
      .get(API_URL)
      .then((response) => {
        if (response.data && Array.isArray(response.data.data)) {
          setBudgetBuilds(response.data.data);
        } else {
          setError("Invalid API response format.");
          setBudgetBuilds([]);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError("Unable to load budget builds. Please try again later.");
        setLoading(false);
      });
  }, []);

  // Fetch products data
  useEffect(() => {
    axios
      .get("http://localhost:5000/api/products")
      .then((response) => {
        const lookup = {};
        response.data.forEach((product) => {
          lookup[product._id] = product;
        });
        setProductsLookup(lookup);
      })
      .catch((err) => {
        console.error("Error fetching products:", err);
      });
  }, []);

  // Scroll to top button visibility
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300);
    };
    
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Handle the comparison button click
  const handleCompareClick = (build) => {
    setSelectedBuilds((prevSelected) => {
      if (prevSelected.some((selected) => selected._id === build._id)) {
        return prevSelected.filter((selected) => selected._id !== build._id);
      } else if (prevSelected.length < 2) {
        return [...prevSelected, build];
      }
      return prevSelected;
    });
  };

  const isBuildSelected = (buildId) => {
    return selectedBuilds.some((build) => build._id === buildId);
  };

  // Navigate to budget build details
  const handleNavigate = useCallback(
    (id) => {
      navigate(`/budget-builds/${id}`);
    },
    [navigate]
  );

  // Helper: Retrieve product description from the lookup if available
  const getProductDescription = (productId, fallback) => {
    return productsLookup[productId]
      ? productsLookup[productId].description
      : fallback;
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  };

  // Return the .value for a given spec key, or null if not found
const getProductSpec = (productId, key) => {
  const product = productsLookup[productId];
  if (!product?.specs) return null;
  const specObj = product.specs.find(s => s.key === key);
  return specObj ? specObj.value : null;
};

// Safely extract the leading integer from any spec value, else 0
const parseSpecNumber = (specValue) => {
  if (typeof specValue !== "string") return 0;
  const m = specValue.match(/(\d+)/);
  return m ? parseInt(m[1], 10) : 0;
};

// Then wrap your ram-capacity lookup in another helper
const getRamCapacityGB = (productId) => {
  const raw = getProductSpec(productId, "ramCapacity");
  return parseSpecNumber(raw);
};

// In your BudgetBuilds component, alongside getRamCapacityGB:
// Safely extract storage capacity in GB from specs (e.g. “500GB”, “1.5 TB”, “2 nas drive bays” → tries to pull “500GB” or “1.5 TB”)
// e.g. just above your component’s return:
const getStorageCapacityGB = (productId) => {
  const raw = getProductSpec(productId, "storageCapacity");
  if (typeof raw !== "string") return 0;
  const m = raw.match(/([\d.]+)\s*(GB|TB)/i);
  if (!m) return 0;
  const num = parseFloat(m[1]);
  const unit = m[2].toUpperCase();
  return unit === "TB" ? num * 1024 : num;
};

const getPowerSupplyWattage = (productId) => {
  // look up the raw spec value, e.g. "750W" or "650 W"
  const raw =
    getProductSpec(productId, "wattage") ||
    getProductSpec(productId, "powerOutput");
  if (typeof raw !== "string") return 0;
  const m = raw.match(/(\d+)\s*W/i);
  return m ? parseInt(m[1], 10) : 0;
};
return (
  <div className={`min-h-screen ${isDark ? "bg-gray-900 text-white" : "bg-gray-50 text-gray-900"}`}>
    {/* Hero Section */}
    <div className={`relative overflow-hidden ${isDark ? "bg-gradient-to-r from-purple-900 to-blue-900" : "bg-gradient-to-r from-blue-500 to-purple-600"} py-20`}>
      <div className="absolute inset-0 opacity-60">
        <div className="absolute inset-0 bg-transparent opacity-10" />
        <div className="h-full w-full bg-[url('https://images.unsplash.com/photo-1551033541-2075d8363c66?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')] bg-cover bg-center" />
      </div>
      <div className="container mx-auto px-4 relative z-10">                      
    <div className="text-8xl flex flex-col items-center text-transparent bg-clip-text bg-gradient-to-r from-green-400 via-lime-400 to-teal-500 mb-4">
    <div className="relative group">
  {/* Main text with cyberpunk color scheme */}
  <span className="font-bold text-8xl mb-1 tracking-tight inline-block
    bg-clip-text text-transparent bg-gradient-to-r from-green-400 via-lime-400 to-teal-500
    relative z-10"
  > Budget Builds </span>
  <div className="absolute -bottom-2 left-0 w-full h-px bg-lime-400"></div>  
  {/* Subtle tech glow effect */}
  <div className="absolute inset-0 bg-cyan-400 opacity-20 blur-md z-0
    transform scale-105 group-hover:opacity-30 transition-opacity duration-300"></div>
</div>
  </div>          <p className="text-xl text-center text-white/90 mb-6 max-w-3xl mx-auto  ">
          Discover Balanced Performance Budget Builds Tailored for Handle Everday Workload            
          </p>
 <div className="flex flex-col md:flex-row items-center justify-center gap-6 p-8 rounded-lg">
    {/* Explore Builds Button */}
    <button
      onMouseEnter={() => setHoverExplore(true)}
      onMouseLeave={() => setHoverExplore(false)}
      onClick={() => window.scrollTo({ top: window.innerHeight - 100, behavior: "smooth" })}
      className={`relative overflow-hidden bg-gradient-to-r from-blue-800 to-fuchsia-800 text-white font-bold px-15 py-6 rounded-lg border-2 border-blue-400 shadow-lg transform transition-all duration-300 ${hoverExplore ? 'scale-105' : ''}`}
    >
      <div className="absolute inset-0 bg-blue-500 opacity-10"></div>
      <div className="absolute top-0 left-0 w-full h-px bg-white opacity-30"></div>
      <div className="absolute bottom-0 right-0 w-full h-px bg-blue-300 opacity-30"></div>
      <div className="flex items-center justify-center gap-2">
        <Cpu size={20} className={`transition-all duration-300 ${hoverExplore ? 'text-blue-300' : 'text-blue-400'}`} />
        <span className="relative z-10">EXPLORE BUILDS</span>
      </div>
    </button>

    {/* Enhanced Cyberpunk AI Build Suggestor Button */}
    <div className="relative group">
      {/* Expanded outer glow effect on hover */}
      <div className={`absolute -inset-1 bg-gradient-to-r from-pink-600 via-cyan-500 to-purple-600 rounded-lg blur transition-all duration-300 
        ${hoverAI ? 'opacity-100 -inset-3 blur-md' : 'opacity-75'} 
        ${glitchEffect ? 'scale-110' : ''} 
        animate-pulse`}
      ></div>
      
      {/* Extra outer glow ring that appears only on hover */}
      <div className={`absolute -inset-3 bg-gradient-to-r from-cyan-600 to-pink-600 rounded-lg blur-lg transition-all duration-500 
        ${hoverAI ? 'opacity-50' : 'opacity-0'}`}
      ></div>
      
      {/* Digital noise overlay */}
      <div className={`absolute inset-0 bg-black opacity-10 
        ${glitchEffect ? 'translate-x-1' : ''} 
        ${hoverAI ? 'bg-gradient-to-r from-black via-transparent to-black' : ''} 
        transition-all duration-100`}
      ></div>
      
      {/* Button with cyberpunk aesthetics */}
      <button
        onMouseEnter={() => setHoverAI(true)}
        onMouseLeave={() => setHoverAI(false)}
        onClick={() => navigate('/AI-build-suggestor')}
        className={`relative bg-black text-cyan-400 font-mono font-bold px-15 py-6 rounded-md border transform transition-all duration-300 overflow-hidden
          ${hoverAI ? 'border-pink-500 shadow-lg shadow-pink-500/50 scale-105' : 'border-cyan-500'} 
          ${glitchEffect ? '-translate-x-px translate-y-px' : ''}`}
      >
        {/* Moving tech grid background that activates on hover */}
        <div className={`absolute inset-0 bg-grid-pattern opacity-20 transition-all duration-1000
          ${hoverAI ? 'animate-grid-move' : ''}`}></div>
        
        {/* Scanline effect intensifies on hover */}
        <div className={`absolute inset-0 bg-gradient-to-b from-transparent via-cyan-900 to-transparent opacity-5 bg-repeat-y bg-size-200 
          ${hoverAI ? 'animate-scanline-fast' : 'animate-scanline'}`}></div>
        
        {/* Warning stripes that appear on hover */}
        <div className={`absolute -left-0 top-0 bottom-0 w-2 bg-warning-stripes transition-all duration-300
          ${hoverAI ? 'opacity-90' : 'opacity-0'}`}></div>
        <div className={`absolute -right-0 top-0 bottom-0 w-2 bg-warning-stripes transition-all duration-300
          ${hoverAI ? 'opacity-90' : 'opacity-0'}`}></div>
        
        {/* Circuit lines that light up more on hover */}
        <div className={`absolute top-0 left-0 w-full h-px transition-all duration-300
          ${hoverAI ? 'bg-cyan-300 opacity-100 shadow-glow-cyan' : 'bg-cyan-600 opacity-70'}`}></div>
        <div className={`absolute top-0 right-4 w-px h-4 transition-all duration-300
          ${hoverAI ? 'bg-cyan-300 opacity-100 shadow-glow-cyan' : 'bg-cyan-600 opacity-70'}`}></div>
        <div className={`absolute top-4 right-0 w-4 h-px transition-all duration-300
          ${hoverAI ? 'bg-cyan-300 opacity-100 shadow-glow-cyan' : 'bg-cyan-600 opacity-70'}`}></div>
        <div className={`absolute bottom-0 right-0 w-full h-px transition-all duration-300
          ${hoverAI ? 'bg-pink-400 opacity-100 shadow-glow-pink' : 'bg-pink-600 opacity-70'}`}></div>
        <div className={`absolute bottom-0 left-4 w-px h-4 transition-all duration-300
          ${hoverAI ? 'bg-pink-400 opacity-100 shadow-glow-pink' : 'bg-pink-600 opacity-70'}`}></div>
        <div className={`absolute bottom-4 left-0 w-4 h-px transition-all duration-300
          ${hoverAI ? 'bg-pink-400 opacity-100 shadow-glow-pink' : 'bg-pink-600 opacity-70'}`}></div>
        
        {/* Text and icons */}
        <div className="flex items-center justify-center gap-2 relative z-10">
          {/* Icon that changes on hover */}
          {hoverAI ? (
            <AlertTriangle 
              size={27} 
              className="text-yellow-400 animate-pulse" 
              style={{ filter: 'drop-shadow(0 0 3px #eab308)' }}
            />
          ) : (
            <Zap 
              size={27} 
              className="text-pink-500" 
              style={{ filter: 'drop-shadow(0 0 2px #ec4899)' }}
            />
          )}
          
          {/* Text that glitches and changes on hover */}
          <span 
            className={`tracking-wider transition-all duration-300 ${glitchText ? 'text-pink-500 skew-x-3' : ''} 
              ${hoverAI ? 'text-cyan-300 font-extrabold tracking-widest' : 'text-cyan-400'}`}
            style={{ 
              textShadow: hoverAI ? '0 0 8px rgba(34, 211, 238, 0.9), 0 0 2px rgba(255, 255, 255, 0.7)' : '0 0 5px rgba(34, 211, 238, 0.7)' 
            }}
          >
            {hoverAI ? ">> ACTIVATE <<" : "AI_BUILD.SYS"}
          </span>
          
          {/* Blinking indicator that speeds up on hover */}
          <div className="absolute -right-2 -top-2 flex items-center justify-center w-4 h-4">
            <div className={`absolute w-2 h-2 bg-cyan-400 rounded-full ${hoverAI ? 'animate-ping-fast' : 'animate-ping'}`}></div>
            <div className={`w-1 h-1 rounded-full transition-colors duration-300 ${hoverAI ? 'bg-cyan-300' : 'bg-cyan-500'}`}></div>
          </div>
        </div>
        
        {/* Digital counters/data that change on hover */}
        <div className={`absolute bottom-1 right-3 text-sm font-mono opacity-70 transition-all duration-300
          ${hoverAI ? 'text-pink-500 text-sm' : 'text-cyan-500 text-xs'}`}>
          {hoverAI ? "READY" : Math.floor(Math.random() * 9999).toString().padStart(3, '0')}
        </div>
        
        {/* Status indicators that appear on hover */}
        <div className={`absolute top-1 left-3 text-sm font-mono transition-all duration-300
          ${hoverAI ? 'opacity-100 text-yellow-400' : 'opacity-0'}`}>
          SYS:ON
        </div>
      </button>
    </div>

    {/* Add some custom CSS for special effects */}
    <style jsx>{`
      @keyframes scanline {
        0% { background-position: 0 -100vh; }
        100% { background-position: 0 100vh; }
      }
      
      @keyframes scanline-fast {
        0% { background-position: 0 -100vh; }
        100% { background-position: 0 100vh; }
      }
      
      @keyframes grid-move {
        0% { background-position: 0 0; }
        100% { background-position: 50px 50px; }
      }
      
      @keyframes ping-fast {
        0% { transform: scale(1); opacity: 1; }
        75%, 100% { transform: scale(2); opacity: 0; }
      }
      
      .animate-scanline {
        animation: scanline 8s linear infinite;
      }
      
      .animate-scanline-fast {
        animation: scanline 4s linear infinite;
      }
      
      .animate-grid-move {
        animation: grid-move 3s linear infinite;
      }
      
      .animate-ping-fast {
        animation: ping-fast 1s cubic-bezier(0, 0, 0.2, 1) infinite;
      }
      
      .bg-size-200 {
        background-size: 100% 8px;
      }
      
      .bg-grid-pattern {
        background-image: 
          linear-gradient(to right, rgba(6, 182, 212, 0.1) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(6, 182, 212, 0.1) 1px, transparent 1px);
        background-size: 20px 20px;
      }
      
      .bg-warning-stripes {
        background-image: repeating-linear-gradient(
          -45deg,
          #f59e0b,
          #f59e0b 10px,
          #000000 10px,
          #000000 20px
        );
      }
      
      .shadow-glow-cyan {
        box-shadow: 0 0 5px rgba(6, 182, 212, 0.7);
      }
      
      .shadow-glow-pink {
        box-shadow: 0 0 5px rgba(236, 72, 153, 0.7);
      }
    `}
    </style>
        </div>
      </div>
    </div>    

      {/* Theme Toggle Button */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 bg-gray-800 text-white p-3 rounded-full shadow-lg transition-all hover:bg-gray-700 focus:outline-none"
      >
        {isDark ? <FaSun className="text-yellow-500" /> : <FaMoon className="text-blue-400" />}
      </button>

      {/* Scroll to top button */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 z-50 bg-blue-600 text-white p-3 rounded-full shadow-lg transition-all hover:bg-blue-700 focus:outline-none"
          aria-label="Scroll to top"
        >
          <FaChevronUp />
        </button>
      )}

      <div className="container mx-auto px-6 py-16">

        {/* Loading States */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-md">
            <p className="font-semibold">Error</p>
            <p>{error}</p>
          </div>
        ) : budgetBuilds.length === 0 ? (
          <div className="text-center p-10 bg-gray-100 rounded-lg">
            <p className="text-xl font-semibold text-gray-600">No budget builds available at the moment.</p>
            <p className="mt-2 text-gray-500">Please check back later for new builds.</p>
          </div>
        ) : (
          <motion.div 
            className="grid sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 w-full mx-auto mb-10"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {budgetBuilds.map((build) => (
              <motion.div
                key={build._id}
                variants={itemVariants}
                className=
                {`cursor-pointer group rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 ${
                  isDark ? "bg-gray-800 hover:bg-gray-750" : "bg-white hover:bg-gray-50"
                }`}
                onClick={(e) => handleNavigate(build._id)}
                
              >
                <div className="relative overflow-hidden">
                  <img
                    src={build.image || "https://via.placeholder.com/800x600?text=Budget+Build"}
                    alt={build.category}
                    className="w-full h-80 object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div 
                    className={`absolute bottom-0 left-0 right-0 p-4 transform translate-y-full group-hover:translate-y-0 transition-transform duration-300 text-white`}
                    onClick={(e) => handleNavigate(build._id)}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNavigate(build._id);
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg mr-2 transition-all"
                    >
                      View Details
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCompareClick(build);
                      }}
                      className={`px-4 py-2 rounded-lg transition-all ${
                        isBuildSelected(build._id)
                          ? "bg-green-600 hover:bg-green-700 text-white"
                          : "bg-gray-200 hover:bg-gray-300 text-gray-800"
                      }`}
                    >
                      {isBuildSelected(build._id) ? "Selected" : "Compare"}
                    </button>
                  </div>
                      <button                      
                      className={`px-6 py-2 rounded-lg transition-all ${
                        isBuildSelected(build._id)
                          ? "bg-green-600 hover:bg-green-700 text-white"
                          : "bg-gray-200 hover:bg-gray-300 text-gray-800"
                      }`}
                    >
                      {isBuildSelected(build._id) ? "" : ""}
                    </button>
                </div>
                
                <div className="text-xl p-6" onClick={() => handleNavigate(build._id)}>
                  <div className="flex justify-between items-start mb-3">
                    <h2 className="text-2xl font-bold">{build.description}</h2>
                    <span className="text-xl font-mono font text-blue-600">{formatPrice(build.price)}</span>
                  </div>
                  <p className={`mb-4 ${isDark ? "text-gray-300" : "text-gray-600"}`}>{build.category}</p>
                  
                  <div className={`mt-4 pt-4 border-t ${isDark ? "border-gray-700" : "border-gray-200"}`}>
                    <div className="grid grid-cols-2 gap-2">
                      <div className={`text-lg ${isDark ? "text-gray-400" : "text-gray-600"}`}>
                        <span className="font-medium">Processor:</span>
                        <p className="truncate">{getProductDescription(build.processor, "High-performance CPU")}</p>
                      </div>
                      <div className={`text-lg ${isDark ? "text-gray-400" : "text-gray-600"}`}>
                        <span className="font-medium">GPU:</span>
                        <p className="truncate">{getProductDescription(build.gpu, "Budget Graphics")}</p>
                      </div>                      
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Comparison Modal */}
      {selectedBuilds.length === 2 && (() => {
        const [firstBuild, secondBuild] = selectedBuilds;

        const chartData = [
          {
            name: "Price (LKR)",
            [firstBuild.description]: firstBuild.price,
            [secondBuild.description]: secondBuild.price,
          },
          {
            name: "RAM (GB)",
            [firstBuild.description]: getRamCapacityGB(firstBuild.ram),
            [secondBuild.description]: getRamCapacityGB(secondBuild.ram),
          },
          
          {
            name: "Storage (GB)",
            [firstBuild.description]: getStorageCapacityGB(firstBuild.storage),
            [secondBuild.description]: getStorageCapacityGB(secondBuild.storage),
          },
          {
            name: "Power Supply (W)",
            [firstBuild.description]: getPowerSupplyWattage(firstBuild.psu),
            [secondBuild.description]: getPowerSupplyWattage(secondBuild.psu),
          },
        ];

        return (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className={`p-6 rounded-xl shadow-2xl w-11/12 max-w-6xl max-h-[90vh] overflow-y-auto ${
              isDark ? "bg-gradient-to-br from-gray-900 to-sky-600 p-6 rounded-xl border border-sky-500/30-gray-900" : "bg-gradient-to-br from-sky-500 to-gray-800 p-6 rounded-xl border border-sky-500/30"
            }`}
          >
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold">Build Comparison</h2>
              <button
                onClick={() => setSelectedBuilds([])}
                className="p-2 rounded-full bg-bg-gray-200 hover:bg-red-600 transition-colors"
                aria-label="Close comparison"
              >
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

              {/* Build Cards */}
              <div className="grid md:grid-cols-2 gap-8">
                {[firstBuild, secondBuild].map((build) => (
                  <div
                    key={build._id}
                    className={`rounded-xl overflow-hidden shadow-lg ${
                      isDark ? "bg-gray-800" : "bg-white"
                    }`}
                  >
                    <img
                      src={build.image || "https://via.placeholder.com/800x600?text=Budget+Build"}
                      alt={build.category}
                      className="w-full h-80 object-cover"
                    />
                    <div className="p-5">
                      <h3 className="text-2xl font-bold mb-2">{build.description}</h3>
                      <p className="text-xl font-mono font-bold text-green-500 mb-6">
                        {formatPrice(build.price)}
                      </p>
                      <div className={`p-4 rounded-lg mb-4 ${isDark ? "bg-gray-700" : "bg-sky-200"}`}>
                        <h4 className="text-xl font-bold mb-3 border-b pb-2">Specifications</h4>
                        {[
                          { label: "Processor :", value: getProductDescription(build.processor, build.processor) },
                          { label: "GPU :", value: getProductDescription(build.gpu, build.gpu) },
                          { label: "RAM :", value: getProductDescription(build.ram, build.ram) },
                          { label: "Storage :", value: getProductDescription(build.storage, build.storage) },
                          { label: "Power Supply :", value: getProductDescription(build.powerSupply, build.powerSupply) },
                          { label: "Casing :", value: getProductDescription(build.casings, build.casings) }
                        ].map((spec, i) => (
                          <div key={i} className="flex mb-3 mt-5">
                            <span className={`font-black ${isDark ? "text-purple-200" : "text-gray-700"}`}>
                              {spec.label}
                            </span>
                            <span className={`ml-3 ${isDark ? "text-gray-200" : "text-gray-600"}`}>
                              {spec.value}
                            </span>
                          </div>
                        ))}
                      </div>
                      <button
                        onClick={() => handleNavigate(build._id)}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium transition-colors"
                      >
                        View Build Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Specs Comparison Chart */}
              {/* Price Comparison */}
              <div className="mt-8">
                <h3 className="text-xl font-bold mb-4 text-center">Price Comparison (LKR)</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={[
                      { name: firstBuild.description, value: firstBuild.price },
                      { name: secondBuild.description, value: secondBuild.price },
                    ]}
                    margin={{ top: 10, right: 20, left: 0, bottom: 5 }}
                  >
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(val) =>
                      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'LKR' }).format(val)
                    }/>
                    <Bar dataKey="value" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* RAM Comparison */}
              <div className="mt-12">
                <h3 className="text-xl font-bold mb-4 text-center">RAM Comparison (GB)</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={[
                      { name: firstBuild.description, value: getRamCapacityGB(firstBuild.ram) },
                      { name: secondBuild.description, value: getRamCapacityGB(secondBuild.ram) },
                    ]}
                    margin={{ top: 10, right: 20, left: 0, bottom: 5 }}
                  >
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            {/* Storage Comparison */}

<div className="mt-12">
  <h3 className="text-xl font-bold mb-4 text-center">Storage Comparison (GB)</h3>
  <ResponsiveContainer width="100%" height={200}>
    <BarChart
      data={[
        {
          name: firstBuild.description,
          value: getStorageCapacityGB(firstBuild.storage),
        },
        {
          name: secondBuild.description,
          value: getStorageCapacityGB(secondBuild.storage),
        },
      ]}
      margin={{ top: 10, right: 20, left: 0, bottom: 5 }}
    >
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip formatter={(val) => `${val} GB`} />
      <Bar dataKey="value" />
    </BarChart>
  </ResponsiveContainer>
</div>

{/* PSU Comparison */}
<div className="mt-12">
  <h3 className="text-xl font-bold mb-4 text-center">
    Power Supply Comparison (W)
  </h3>
  <ResponsiveContainer width="100%" height={200}>
    <BarChart
      data={[
        {
          name: firstBuild.description,
          value: getPowerSupplyWattage(firstBuild.powerSupply),
        },
        {
          name: secondBuild.description,
          value: getPowerSupplyWattage(secondBuild.powerSupply),
        },
      ]}
      margin={{ top: 10, right: 20, left: 0, bottom: 5 }}
    >
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip formatter={(val) => `${val} W`} />
      <Bar dataKey="value" />
    </BarChart>
  </ResponsiveContainer>
</div>
            </motion.div>
          </div>
        );
      })()}
    </div>
  );
};

export default BudgetBuilds;