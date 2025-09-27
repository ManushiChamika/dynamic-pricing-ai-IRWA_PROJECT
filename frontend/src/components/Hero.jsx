import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import home4 from '../assets/home1.png';

// Import icons from react-icons
import { MdLaptop, MdMonitor, MdKeyboard, MdMouse, MdStorage } from 'react-icons/md';
import { FaMicrochip, FaVolumeUp, FaHdd, FaPlug, FaFan } from 'react-icons/fa';
import { GiCircuitry, GiBatteryPack } from 'react-icons/gi';
import { BsFillMotherboardFill } from "react-icons/bs";
import { RiRamLine } from "react-icons/ri";
import { LuPcCase } from "react-icons/lu";

const sidebarItems = [
  { label: 'Laptop', path: 'laptop', icon: <MdLaptop className="text-4xl" /> },
  { label: 'Motherboard', path: 'motherboards', icon: <BsFillMotherboardFill className="text-4xl" /> },
  { label: 'Processor', path: 'processor', icon: <FaMicrochip className="text-4xl" /> },
  { label: 'RAM', path: 'ram', icon: <RiRamLine className="text-4xl" /> },
  { label: 'Graphic Cards', path: 'gpu', icon: <GiCircuitry className="text-4xl" /> },
  { label: 'Power Supply Units', path: 'powerSupply', icon: <FaPlug className="text-4xl" /> },
  { label: 'Casings', path: 'casings', icon: <LuPcCase className="text-4xl" /> },
  { label: 'Monitors', path: 'monitors', icon: <MdMonitor className="text-4xl" /> },
  { label: 'CPU Coolers / AIO', path: 'cpu coolers', icon: <FaFan className="text-4xl" /> },
  { label: 'Keyboard', path: 'keyboard', icon: <MdKeyboard className="text-4xl" /> },
  { label: 'Mouse', path: 'mouse', icon: <MdMouse className="text-4xl" /> },
  { label: 'Sound Systems', path: 'sound systems', icon: <FaVolumeUp className="text-4xl" /> },
  { label: 'Cables & Connectors', path: 'cables and connectors', icon: <FaPlug className="text-4xl" /> },
  { label: 'Storage', path: 'storage', icon: <MdStorage className="text-4xl" /> },
  { label: 'External Storage', path: 'external storage', icon: <FaHdd className="text-4xl" /> },
];


const Hero = () => {
  const navigate = useNavigate();
  const [hoveredItem, setHoveredItem] = useState(null);
  const [filters, setFilters] = useState([]);

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/filters');
        const data = await res.json();
        setFilters(data);
      } catch (error) {
        console.error('Error fetching filters:', error);
      }
    };

    fetchFilters();
  }, []);

  const handleCategoryClick = (category) => {
    navigate(`/products/${category}`);
  };

  const handleCustomPreBuildsClick = () => {
    window.scrollTo(0, 0);
  };

  return (
    <div className="bg-black text-white min-h-screen flex mb-auto">
      {/* Sidebar */}
      <aside className="bg-black p-3 h-screen max-h-[80vh] overflow-y-auto custom-scrollbar">
        <nav className="flex flex-col space-y-2">
          <button
            onClick={() => navigate('/AI-Engine')}
            className="group relative bg-gradient-to-r from-red-900 to-blue-700 text-white flex flex-col p-5 px-10 overflow-hidden"
            style={{
              borderRadius: '8px',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            {/* Animated background effect */}
            <div
              className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxkZWZzPgogICAgPHBhdHRlcm4gaWQ9ImNpcmN1aXQiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiIHdpZHRoPSI1MCIgaGVpZ2h0PSI1MCIgdmlld0JveD0iMCAwIDUwIDUwIj4KICAgICAgPHJlY3QgeD0iMCIgeT0iMCIgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0icmdiYSgwLDAsMCwwKSIgLz4KICAgICAgPHBhdGggZD0iTTAgMTAgTDEwIDEwIE0yMCAxMCBMMzAgMTAgTTQwIDEwIEw1MCAxMCBNMTAgMCBMMTAgMTAgTTEwIDIwIEwxMCAzMCBNMTAgNDAgTDEwIDUwIE0zMCAwIEwzMCAxMCBNMzAgMjAgTDMwIDMwIE0zMCAzNSBMMzUgMzUgTTMwIDQwIEwzMCA1MCBNNDAgMzUgTDQ1IDM1IE01MCAzNSBMMzUgNTAgTTAgMzUgTDUgMzUgTTUwIDM1IEwzNSA1MCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIgc3Ryb2tlLXdpZHRoPSIxIiAvPgogICAgPC9wYXR0ZXJuPgogIDwvZGVmcz4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2NpcmN1aXQpIiAvPgo8L3N2Zz4=')]"
              style={{ opacity: 0.2 }}
            ></div>
            {/* Subtle scanning light effect */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-400 to-transparent opacity-70 scanning-light"></div>
            <div
              className="mt-2 text-3xl text-center py-2"
              style={{
                background: 'linear-gradient(to right, #ffffff, #a0e9ff)',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
                fontStyle: 'italic',
                fontWeight: 'bold',
                textShadow: '0 0 10px rgba(135, 206, 250, 0.5)'
              }}
            >
              <div className="uppercase flex items-center justify-center">
                <span className="mr-2">The</span>
                <span>AI</span>
                <span className="ml-2">Engine</span>
              </div>
            </div>
            {/* Interactive hover effect */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-gradient-to-r from-red-600/20 to-blue-600/20 transition-opacity duration-300"></div>
          </button>

          <br />

          {/* Dynamically render category items */}
          {filters.map((filter, index) => (
            <button
              key={index}
              onClick={() => handleCategoryClick(filter.category)}
              onMouseEnter={() => setHoveredItem(index)}
              onMouseLeave={() => setHoveredItem(null)}
              className="group relative bg-gray-900/60 text-white flex w-full justify-start p-5 cursor-pointer rounded-md overflow-hidden border border-transparent hover:border-blue-500/30 transition-all duration-300"
            >
              {/* Animated glow effect on hover */}
              <div
                className={`absolute inset-0 bg-gradient-to-r from-blue-600/0 via-blue-600/10 to-blue-600/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
                  hoveredItem === index ? 'animate-pulse-slow' : ''
                }`}
              ></div>
              <div className="relative flex items-center justify-between w-full">
                <span className="uppercase text-gray-300 group-hover:text-white transition-all duration-300">
                  {filter.category}
                </span>
              </div>
              {/* Subtle left border indicator */}
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-400 via-blue-500 to-blue-400 scale-y-0 group-hover:scale-y-100 transition-transform duration-300 origin-center"></div>
            </button>
          ))}

          <div className="h-0.5 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent my-4"></div>

          {/* Custom Pre-builds Button */}
          <Link 
            to="/custom-prebuilds" 
            onClick={handleCustomPreBuildsClick} 
            className="relative bg-gradient-to-br from-gray-900 via-blue-900 to-blue-800 text-gray-100 flex flex-col items-center p-4 text-lg rounded-lg shadow-lg cursor-pointer transition-all duration-500 overflow-hidden group hover:shadow-xl hover:shadow-blue-500/30 hover:scale-105"
          >
            {/* Circuit pattern background */}
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxkZWZzPgogICAgPHBhdHRlcm4gaWQ9ImNpcmN1aXQyIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIiB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCI+CiAgICAgIDxyZWN0IHg9IjAiIHk9IjAiIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InJnYmEoMCwwLDAsMCkiIC8+CiAgICAgIDxwYXRoIGQ9Ik0wIDIwIEwyMCAyMCBNMTAgMCBMMTAgNTAgTTMwIDAgTDMwIDUwIE00MCAzMCBMNjAgMzAgTTUwIDAgTDUwIDYwIE0wIDQwIEw2MCA0MCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLW9wYWNpdHk9IjAuMDgiIHN0cm9rZS13aWR0aD0iMSIgLz4KICAgICAgPGNpcmNsZSBjeD0iMTAiIGN5PSIyMCIgcj0iMiIgZmlsbD0id2hpdGUiIGZpbGwtb3BhY2l0eT0iMC4xIiAvPgogICAgICA8Y2lyY2xlIGN4PSIzMCIgY3k9IjQwIiByPSIyIiBmaWxsPSJ3aGl0ZSIgZmlsbC1vcGFjaXR5PSIwLjEiIC8+CiAgICAgIDxjaXJjbGUgY3g9IjUwIiBjeT0iMzAiIHI9IjIiIGZpbGw9IndoaXRlIiBmaWxsLW9wYWNpdHk9IjAuMSIgLz4KICAgIDwvcGF0dGVybj4KICA8L2RlZnM+CiAgPHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNjaXJjdWl0MikiIC8+Cjwvc3ZnPg==')]" 
            style={{ opacity: 0.15 }}
          ></div>
          {/* Sliding glow effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-400/20 to-transparent -translate-x-full animate-shimmer"></div>
          {/* Hover glow effect */}
          <div className="absolute inset-0 bg-blue-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg"></div>
          {/* Subtle border glow */}
          <div className="absolute inset-0 rounded-lg border border-blue-400/20 group-hover:border-blue-400/50 transition-colors duration-300"></div>
          <div className="mt-2 text-3xl italic font-bold relative z-10 bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent group-hover:from-blue-100 group-hover:to-white transition-all duration-300">
            Custom Pre-builds
          </div>
          <p className="text-gray-300 relative z-10 group-hover:text-blue-100 mt-1">
            - Build your dream PC -
          </p>
        </Link>
        </nav>
      </aside>

      {/* Main Hero Content */}
      <div className="flex-1 relative overflow-hidden">
        {/* Animated tech background overlay */}
        <div
          className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxkZWZzPgogICAgPHBhdHRlcm4gaWQ9ImdyaWQiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+CiAgICAgIDxyZWN0IHg9IjAiIHk9IjAiIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InJnYmEoMCwwLDAsMCkiIC8+CiAgICAgIDxwYXRoIGQ9Ik0xMCAwIEwxMCAxMDAgTTIwIDAgTDIwIDEwMCBNMzAgMCBMMzAgMTAwIE00MCAwIEw0MCAxMDAgTTUwIDAgTDUwIDEwMCBNNjAgMCBMNjAgMTAwIE03MCAwIEw3MCAxMDAgTTgwIDAgTDgwIDEwMCBNOTAgMCBMOTAgMTAwIE0wIDEwIEwxMDAgMTAgTTAgMjAgTDEwMCAyMCBNMCAzMCBMMTAwIDMwIE0wIDQwIEwxMDAgNDAgTTAgNTAgTDEwMCA1MCBNMCAwIEwxMDAgMTAwIE0xMDAgMCBMMCAxMDAiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjAzIiBzdHJva2Utd2lkdGg9IjAuNSIgLz4KICAgICAgPGNpcmNsZSBjeD0iMTAiIGN5PSIxMCIgcj0iMSIgZmlsbD0id2hpdGUiIGZpbGwtb3BhY2l0eT0iMC4xIiAvPgogICAgICA8Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIxIiBmaWxsPSJ3aGl0ZSIgZmlsbC1vcGFjaXR5PSIwLjEiIC8+CiAgICAgIDxjaXJjbGUgY3g9IjUwIiBjeT0iNTAiIHI9IjEiIGZpbGw9IndoaXRlIiBmaWxsLW9wYWNpdHk9IjAuMSIgLz4KICAgICAgPGNpcmNsZSBjeD0iNzAiIGN5PSI3MCIgcj0iMSIgZmlsbD0id2hpdGUiIGZpbGwtb3BhY2l0eT0iMC4xIiAvPgogICAgICA8Y2lyY2xlIGN4PSI5MCIgY3k9IjkwIiByPSIxIiBmaWxsPSJ3aGl0ZSIgZmlsbC1vcGFjaXR5PSIwLjEiIC8+CiAgICA8L3BhdHRlcm4+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiIC8+Cjwvc3ZnPg==')]"
          style={{ opacity: 0.15 }}
        ></div>

        {/* Main content with image */}
        <div className="container mx-auto px-10 pt-9 pb-auto relative">
          {/* Glow effect around image */}
          <div className="relative overflow-hidden rounded-lg shadow-2xl">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 via-transparent to-blue-600 opacity-30 blur-sm"></div>
            <img 
              src={home4} 
              alt="Hero image" 
              className="relative z-10 w-full object-cover transition-all duration-500 hover:scale-105 rounded-lg border border-blue-500/20"
            />
          </div>
        </div>
      </div>

      {/* Custom CSS styles */}
      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        .animate-shimmer {
          animation: shimmer 3s infinite;
        }
        @keyframes scan {
          0%, 100% { transform: translateY(0); opacity: 0; }
          50% { transform: translateY(300%); opacity: 1; }
        }
        .scanning-light {
          animation: scan 4s infinite;
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.1; }
          50% { opacity: 0.3; }
        }
        .animate-pulse-slow {
          animation: pulse-slow 2s infinite;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.1);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #3b82f6, #1e40af);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #60a5fa, #2563eb);
        }
      `}</style>
    </div>
  );
};

export default Hero;
