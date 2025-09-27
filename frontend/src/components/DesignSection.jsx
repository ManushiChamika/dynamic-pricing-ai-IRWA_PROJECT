import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom'; // Ensure you're using 'react-router-dom' for routing
import { HiArrowRight } from 'react-icons/hi';

import { BsPlayFill, BsPauseFill } from 'react-icons/bs';
import { Cpu, Zap, AlertTriangle } from 'lucide-react';
import { useNavigate } from "react-router-dom";

const tabsData = [
  {
    id: 'tab1',
    title: 'Unleash Your Gaming Potential',
    subtitle: 'Fine-tune every detail of your gaming setup, from powerhouse GPUs to lightning-fast SSDs, for an unparalleled experience that crushes lag and elevates every match.',
    video: 'https://res.cloudinary.com/dovdejenw/video/upload/v1742242404/Video%20Files/Custom%20Build/klhr8jxbqsjhhr2is0de.mp4',
    poster: 'https://cdn.prod.website-files.com/66e88746834b80507cdf7933/670570322cf4b274d716fed4_design-without-limits.avif',
    cta: {
      text: 'Discover Custom Builds',
      link: '/custom-prebuilds'
    }
  },
  {
    id: 'tab2',
    title: 'Power Your Passion',
    subtitle: 'Transform your gaming experience adapts to your needs. choose the processor, graphics, and accessories that help you elevate your gameplay to the next level.',
    video: 'https://res.cloudinary.com/dovdejenw/video/upload/v1742242434/Video%20Files/Custom%20Build/g2yhhfmv0hna7fskfxkh.mp4',
    poster: 'https://cdn.prod.website-files.com/66e88746834b80507cdf7933/67057032ad30932a68cd9d18_animations.avif',
    cta: {
      text: 'Discover Premium Gaming Experience',
      link: '/custom-prebuilds'
    }
  },
  {
    id: 'tab3',
    title: 'Efficiency Meets Affordability',
    subtitle: 'Don’t sacrifice quality for cost. With customizable budget pre-builds, you can achieve high-speed performance for work, school, or casual gaming without the hefty price tag.',
    video: 'https://res.cloudinary.com/dovdejenw/video/upload/v1742242473/Video%20Files/Custom%20Build/ymqbpqcb4oaw22ctr4wj.mp4',
    poster: 'https://cdn.prod.website-files.com/66e88746834b80507cdf7933/67058d52036e5522e27966de_build-on-brand.avif',
    cta: {
      text: 'Discover Balanced Efficiency',
      link: '/custom-prebuilds'
    }
  },
  {
    id: 'tab4',
    title: 'Performance on a Budget',
    subtitle: "Achieve reliable performance for both productivity and light gaming with carefully selected components, offering the best value for money without compromising on quality..",
    video: 'https://res.cloudinary.com/dovdejenw/video/upload/v1742242504/Video%20Files/Custom%20Build/zwklhvss0xmo06ceexvy.mp4',
    poster: 'https://cdn.prod.website-files.com/66e88746834b80507cdf7933/670570323f08ce0aed3368e4_ai-assistant.avif',
    cta: {
      text: 'Discover Gaming Solutions',
      link: '/custom-prebuilds'
    }
  },
  {
    id: 'tab5',
    title: 'Empower Your Work & Play',
    subtitle: "From office productivity to light gaming, create a system that is fully tailored to your needs, offering the perfect balance of performance and affordability.",
    video: 'https://res.cloudinary.com/dovdejenw/video/upload/v1742242531/Video%20Files/Custom%20Build/pifmkd6mrlhgvr1vvxqo.mp4',
    poster: 'https://cdn.prod.website-files.com/66e88746834b80507cdf7933/670570323f08ce0aed3368e4_ai-assistant.avif',
    cta: {
      text: 'Discover Ultimate Performance',
      link: '/custom-prebuilds'
    }
  },
  {
    id: 'tab6',
    title: 'Craft Your Dream PC Today',
    subtitle: "Choose the perfect combination of power, speed, and efficiency with our customizable pre-builds. Upgrade and adjust your PC to meet your needs and budget without compromise.",
    video: 'https://res.cloudinary.com/dovdejenw/video/upload/v1742242556/Video%20Files/Custom%20Build/qlew0fmhhge5bhbbqodk.mp4',
    poster: 'https://cdn.prod.website-files.com/66e88746834b80507cdf7933/670570323f08ce0aed3368e4_ai-assistant.avif',
    cta: {
      text: 'Discover your Dream PC',
      link: '/custom-prebuilds'
    }
  }
];

const DesignSection = () => {
  const [activeTab, setActiveTab] = useState('tab1');
  const [isPlaying, setIsPlaying] = useState(true);
  const [progress, setProgress] = useState(0);
  const progressInterval = useRef(null);
  const PROGRESS_DURATION = 10000; // 10 seconds for each tab
  const UPDATE_INTERVAL = 100; // Update progress every 100ms
  const [hoverExplore, setHoverExplore] = useState(false);
  const [hoverAI, setHoverAI] = useState(false);
  const [glitchEffect, setGlitchEffect] = useState(false);
  const [glitchText, setGlitchText] = useState(false);
  const navigate = useNavigate();

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


  useEffect(() => {
    startProgressTimer();
    return () => clearInterval(progressInterval.current);
  }, [activeTab]);

  const startProgressTimer = () => {
    setProgress(0);
    clearInterval(progressInterval.current);

    progressInterval.current = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          // Move to next tab
          const currentIndex = tabsData.findIndex(tab => tab.id === activeTab);
          const nextIndex = (currentIndex + 1) % tabsData.length;
          setActiveTab(tabsData[nextIndex].id);
          return 0;
        }
        return prev + (UPDATE_INTERVAL / PROGRESS_DURATION * 100);
      });
    }, UPDATE_INTERVAL);
  };

  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
    setIsPlaying(true);
    setProgress(0);
  };

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying);
    const video = document.querySelector(`video[data-tab="${activeTab}"]`);
    if (video) {
      if (isPlaying) {
        video.pause();
        clearInterval(progressInterval.current);
      } else {
        video.play();
        startProgressTimer();
      }
    }
  };

  // Function to handle scrolling to the top when navigating
  const handleCustomPreBuildsClick = () => {
    window.scrollTo(0, 0); // Scroll to the top when clicking the Custom Pre-builds link
  };

  return (
    
 <section className="overflow-hidden py24 bg-gradient-to-tr from-gray-900 via-blue-950 to-gray-950 dark:from-black dark:via-gray-900 dark:to-gray-950 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-16 relative z-10">
        
            {/* Header Section with animated reveal */}
    <div className="max-w-[50rem] lg:mb-24 mb-16 relative">
      <div className="absolute -left-8 top-1/2 transform -translate-y-1/2 w-2 h-24 bg-gradient-to-b from-blue-500 to-indigo-600" />
      <h2 className="text-6xl md:text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-100 to-blue-200 mb-8 tracking-tight">
        Your Build - Your Rules
      </h2>
    </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
          <div className='flex flex-col justify-between gap-16'>
            {/* paragraph and button */}
            
               {/* paragraph with modern styling */}
        <p className="text-2xl text-gray-300 leading-relaxed backdrop-blur-sm bg-black/5 p-6 rounded-lg border border-white/10 shadow-lg">
          Unlock solid performance without the high price tag. Choose from budget-friendly yet powerful components that don't compromise on quality. Get the most out of your PC, perfectly tailored to your needs and budget.
        </p>         
              
              <div className="flex mt-8 justify-self-center lg:justify-self-start gap-8 items-center flex-col lg:flex-row lg:gap-8 lg:items-start lg:mt-0 lg:mb-8"> 
                              
                <Link 
  to="/custom-prebuilds" 
  onClick={handleCustomPreBuildsClick} 
  className="relative bg-gradient-to-r from-gray-900 via-blue-500 to-blue-1000 min-w-84 text-gray-100 flex flex-col items-center p-4 text-lg rounded-lg shadow-lg cursor-pointer transition-all duration-300 overflow-hidden group hover:shadow-xl hover:shadow-blue-500/30 hover:scale-105"
>
  {/* Sliding glow effect when idle */}
  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-400/20 to-transparent -translate-x-full animate-shimmer"></div>
  
  {/* Hover glow effect */}
  <div className="absolute inset-0 bg-blue-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg"></div>
  
  {/* Subtle border glow */}
  <div className="absolute inset-0 rounded-lg border border-blue-400/20 group-hover:border-blue-400/50 transition-colors duration-300"></div>
  
  <div className="mt-2 text-3xl italic font-bold relative z-10 group-hover:text-white transition-colors duration-300">Custom Pre-builds</div>
  <p className="text-gray-200 relative z-10 group-hover:text-blue-100">- Build your dream PC -</p>
</Link>

{/* Add this keyframe animation to your CSS or style tag */}
<style jsx>{`
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
  }
  
  .animate-shimmer {
    animation: shimmer 3s infinite;
  }
`}</style>

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
        className={`relative bg-black text-cyan-400 font-mono font-bold px-19 py-9 rounded-md border transform transition-all duration-300 overflow-hidden
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
      
         {/* Tabs Section */}
            <div className="space-y-6">
              {tabsData.map((tab) => (
                <div
                  key={tab.id}
                  className="relative pl-6 cursor-pointer transition-all duration-300 hover:translate-x-1"
                  onClick={() => handleTabClick(tab.id)}
                >
                  {/* Progress bar */}
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-gray-800">
                    {activeTab === tab.id && (
                      <div 
                        className="absolute top-0 left-0 w-full bg-rose-600 transition-all duration-100 shadow-glow"
                        style={{ height: `${progress}%` }}
                      />
                    )}
                  </div>

                  <h3 className={`text-xl font-semibold mb-2 transition-all duration-300 ${
                activeTab === tab.id ? 'text-blue-400' : 'text-white'
              }`}>
                {tab.title}
              </h3>
                  <p className={`text-gray-300 transition-all duration-300 ${
                    activeTab === tab.id ? 'h-auto opacity-100' : 'h-0 opacity-0 overflow-hidden'
                  }`}>
                    {tab.subtitle}
                  </p>
                </div>
              ))}
            </div>
          </div>

           {/* Video Display with enhanced container */}
      <div className="relative">
        <div className="max-w-[700px] mx-auto">
          {/* Decorative corner accents */}
          <div className="absolute -top-2 -left-2 w-8 h-8 border-t-2 border-l-2 border-blue-400/50"></div>
          <div className="absolute -top-2 -right-2 w-8 h-8 border-t-2 border-r-2 border-blue-400/50"></div>
          <div className="absolute bottom-8 -left-2 w-8 h-8 border-b-2 border-l-2 border-blue-400/50"></div>
          <div className="absolute bottom-8 -right-2 w-8 h-8 border-b-2 border-r-2 border-blue-400/50"></div>
          
          {tabsData.map((tab) => (
            <div
              key={tab.id}
              className={`transition-opacity duration-500 relative ${
                activeTab === tab.id ? 'opacity-100' : 'opacity-0 hidden'
              }`}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-indigo-600/20 rounded-lg transform scale-105 blur-md -z-10"></div>
              <video
                data-tab={tab.id}
                src={tab.video}
                poster={tab.poster}
                className="w-full rounded-lg border border-white/10 shadow-xl"
                autoPlay
                muted
                playsInline
                loop
              />
              <div className="flex items-center justify-between mt-6 backdrop-blur-sm bg-black/20 p-4 rounded-lg border border-white/10">
                <Link 
                  to={tab.cta.link}
                  className="inline-flex items-center text-blue-300 hover:text-white transition-colors group"
                >
                  <span className="relative">
                    {tab.cta.text}
                    <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-blue-400 group-hover:w-full transition-all duration-300"></span>
                  </span>
                  <HiArrowRight className="ml-2 transform group-hover:translate-x-1 transition-transform" />
                </Link>
                <button
                  onClick={togglePlayPause}
                  className="p-2 text-white hover:text-blue-300 bg-blue-900/30 rounded-full border border-blue-500/30 transition-all hover:border-blue-500/50"
                >
                  {isPlaying ? <BsPauseFill size={24} /> : <BsPlayFill size={24} />}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
  
  {/* Custom styles for animations */}
  <style jsx>{`
    @keyframes shimmer {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(200%); }
    }
    
    .animate-shimmer {
      animation: shimmer 3s infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 0.5; }
      50% { opacity: 0.8; }
    }
    
    .animate-pulse {
      animation: pulse 4s infinite ease-in-out;
    }
    
    .shadow-glow {
      box-shadow: 0 0 15px rgba(59, 130, 246, 0.6);
    }
  `}</style>
</section>

  );
};

export default DesignSection;