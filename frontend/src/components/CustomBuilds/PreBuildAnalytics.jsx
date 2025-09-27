// React core imports
import React, { useState, useEffect, useMemo, useRef } from "react";
import axios from "axios";
import { Bar, Line, Pie, Radar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, ArcElement, Filler, RadialLinearScale } from "chart.js";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import "jspdf-autotable";

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, RadialLinearScale, Title, Tooltip, Legend, Filler);

const PreBuildAnalytics = () => {
  const [builds, setBuilds] = useState([]);
  const [productsLookup, setProductsLookup] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // References for chart components
  const pieRef = useRef();
  const barRef = useRef();
  const lineRef = useRef();
  const radarRef = useRef();
 
  // Define color scheme constants for consistent theming throughout the app
  const COLORS = {
    primary: {
      blue: 'rgba(59, 130, 246, 1)',      // blue-500
      purple: 'rgba(139, 92, 246, 1)',     // purple-500
      cyan: 'rgba(34, 211, 238, 1)',       // cyan-400
      emerald: 'rgba(52, 211, 153, 1)',    // emerald-400
      green: 'rgba(74, 222, 128, 1)',      // green-400
      pink: 'rgba(244, 114, 182, 1)',      // pink-400
      orange: 'rgba(251, 146, 60, 1)',     // orange-400
      yellow: 'rgba(250, 204, 21, 1)',     // yellow-400
      lime: 'rgba(163, 230, 53, 1)',       // lime-400
      red: 'rgba(248, 113, 113, 1)'        // red-400
    },
    transparent: {
      blue: 'rgba(59, 130, 246, 0.2)',
      purple: 'rgba(139, 92, 246, 0.2)',
      cyan: 'rgba(34, 211, 238, 0.2)',
      emerald: 'rgba(52, 211, 153, 0.2)',
      green: 'rgba(74, 222, 128, 0.2)',
      pink: 'rgba(244, 114, 182, 0.2)',
      orange: 'rgba(251, 146, 60, 0.2)',
      yellow: 'rgba(250, 204, 21, 0.2)',
      lime: 'rgba(163, 230, 53, 0.2)',
      red: 'rgba(248, 113, 113, 0.2)'
    },
    gradients: {
      header: ['#0ea5e9', '#a855f7'],      // cyan-500 to purple-500
      subHeader: ['#10b981', '#3b82f6'],   // emerald-500 to blue-500
      metrics: ['#a855f7', '#ef4444'],     // purple-500 to red-500
      button: ['#2563eb', '#7c3aed']       // blue-600 to purple-600
    }
  };

  // Fetch pre-builds and all products concurrently
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch builds with loading notification
        console.log('📊 Fetching pre-built PC data...');
        const buildsResponse = await axios.get("http://localhost:5000/api/prebuilds");
        setBuilds(buildsResponse.data.data);
        console.log(`✅ Successfully loaded ${buildsResponse.data.data.length} pre-built PCs`);

        // Fetch all products and create a lookup by _id
        console.log('🔍 Fetching product details...');
        const productsResponse = await axios.get("http://localhost:5000/api/products");
        const lookup = {};
        productsResponse.data.forEach((product) => {
          lookup[product._id] = product;
        });
        setProductsLookup(lookup);
        console.log(`✅ Successfully loaded ${Object.keys(lookup).length} products`);
        
        setLoading(false);
      } catch (err) {
        console.error("❌ Error fetching data:", err);
        setError("Failed to load data. Please check your connection and try again.");
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Compute data for charts
  const {
    categoryDistribution,
    priceRanges,
    componentUsage,
    priceByCategory,
    topBuilds,
    componentComparison
  } = useMemo(() => {
    if (builds.length === 0) {
      return {
        categoryDistribution: {},
        priceRanges: {},
        componentUsage: {},
        priceByCategory: [],
        topBuilds: [],
        componentComparison: []
      };
    }

    console.log('🧮 Computing analytics data...');
    
    // Category distribution
    const categoryDist = builds.reduce((acc, build) => {
      acc[build.category] = (acc[build.category] || 0) + 1;
      return acc;
    }, {});

    // Price ranges with prettier labels
    const priceRanges = {
      "LKR 0 - LKR 50K": 0,
      "LKR 50K - LKR 100K": 0,
      "LKR 100K - LKR 150K": 0,
      "LKR 150K - LKR 200K": 0,
      "LKR 200K+": 0
    };

    builds.forEach(build => {
      if (build.price <= 50000) priceRanges["LKR 0 - LKR 50K"]++;
      else if (build.price <= 100000) priceRanges["LKR 50K - LKR 100K"]++;
      else if (build.price <= 150000) priceRanges["LKR 100K - LKR 150K"]++;
      else if (build.price <= 200000) priceRanges["LKR 150K - LKR 200K"]++;
      else priceRanges["LKR 200K+"]++;
    });

    // Component usage
    const components = {
      processor: {},
      gpu: {},
      ram: {},
      storage: {},
      powerSupply: {},
      casings: {}
    };

    builds.forEach(build => {
      // Count processor usage with improved error handling
      const processorId = build.processor;
      const processorName = productsLookup[processorId]?.description || "Unknown Processor";
      if (processorName !== "Unknown Processor") {
        components.processor[processorName] = (components.processor[processorName] || 0) + 1;
      }

      // Count GPU usage
      const gpuId = build.gpu;
      const gpuName = productsLookup[gpuId]?.description || "Unknown GPU";
      if (gpuName !== "Unknown GPU") {
        components.gpu[gpuName] = (components.gpu[gpuName] || 0) + 1;
      }

      // Same for other components with improved error handling
      const ramId = build.ram;
      const ramName = productsLookup[ramId]?.description || "Unknown RAM";
      if (ramName !== "Unknown RAM") {
        components.ram[ramName] = (components.ram[ramName] || 0) + 1;
      }

      const storageId = build.storage;
      const storageName = productsLookup[storageId]?.description || "Unknown Storage";
      if (storageName !== "Unknown Storage") {
        components.storage[storageName] = (components.storage[storageName] || 0) + 1;
      }

      const powerSupplyId = build.powerSupply;
      const powerSupplyName = productsLookup[powerSupplyId]?.description || "Unknown PSU";
      if (powerSupplyName !== "Unknown PSU") {
        components.powerSupply[powerSupplyName] = (components.powerSupply[powerSupplyName] || 0) + 1;
      }

      const casingsId = build.casings;
      const casingsName = productsLookup[casingsId]?.description || "Unknown Case";
      if (casingsName !== "Unknown Case") {
        components.casings[casingsName] = (components.casings[casingsName] || 0) + 1;
      }
    });

    // Price by category
    const priceByCategory = Object.entries(categoryDist).map(([category, count]) => {
      const categoryBuilds = builds.filter(b => b.category === category);
      const totalPrice = categoryBuilds.reduce((sum, b) => sum + b.price, 0);
      const avgPrice = totalPrice / count;
      
      return {
        category,
        count,
        totalPrice,
        avgPrice
      };
    });

    // Top 5 most expensive builds
    const topBuilds = [...builds]
      .sort((a, b) => b.price - a.price)
      .slice(0, 5)
      .map(build => ({
        category: build.category,
        price: build.price,
        processor: productsLookup[build.processor]?.description || "Unknown Processor",
        gpu: productsLookup[build.gpu]?.description || "Unknown GPU"
      }));

    // Component comparison for radar chart (top categories)
    const categories = Object.keys(categoryDist);
    const componentComparison = categories.map(category => {
      const categoryBuilds = builds.filter(b => b.category === category);
      const avgPrice = categoryBuilds.reduce((sum, b) => sum + b.price, 0) / categoryBuilds.length;
      
      // Find most common components in this category
      let mostCommonProcessor = "";
      let mostCommonGpu = "";
      
      const processorCount = {};
      const gpuCount = {};
      
      categoryBuilds.forEach(build => {
        const processorName = productsLookup[build.processor]?.description || "Unknown";
        if (processorName !== "Unknown") {
          processorCount[processorName] = (processorCount[processorName] || 0) + 1;
        }
        
        const gpuName = productsLookup[build.gpu]?.description || "Unknown";
        if (gpuName !== "Unknown") {
          gpuCount[gpuName] = (gpuCount[gpuName] || 0) + 1;
        }
      });
      
      mostCommonProcessor = Object.entries(processorCount).sort((a, b) => b[1] - a[1])[0]?.[0] || "N/A";
      mostCommonGpu = Object.entries(gpuCount).sort((a, b) => b[1] - a[1])[0]?.[0] || "N/A";
      
      return {
        category,
        avgPrice,
        count: categoryBuilds.length,
        mostCommonProcessor,
        mostCommonGpu
      };
    });

    console.log('✅ Analytics computation complete');
    
    return {
      categoryDistribution: categoryDist,
      priceRanges,
      componentUsage: components,
      priceByCategory,
      topBuilds,
      componentComparison
    };
  }, [builds, productsLookup]);

  // Dynamic category colors for consistent UI
  const getCategoryColors = useMemo(() => {
    const categories = Object.keys(categoryDistribution);
    const colorMap = {};
    
    // Assign consistent colors to categories
    const colorPalette = [
      COLORS.primary.blue,
      COLORS.primary.purple,
      COLORS.primary.cyan,
      COLORS.primary.emerald,
      COLORS.primary.pink,
      COLORS.primary.orange,
      COLORS.primary.yellow,
      COLORS.primary.green,
      COLORS.primary.lime,
      COLORS.primary.red
    ];
    
    const transparentPalette = [
      COLORS.transparent.blue,
      COLORS.transparent.purple,
      COLORS.transparent.cyan,
      COLORS.transparent.emerald,
      COLORS.transparent.pink,
      COLORS.transparent.orange,
      COLORS.transparent.yellow,
      COLORS.transparent.green,
      COLORS.transparent.lime,
      COLORS.transparent.red
    ];
    
    categories.forEach((category, index) => {
      const colorIndex = index % colorPalette.length;
      colorMap[category] = {
        solid: colorPalette[colorIndex],
        transparent: transparentPalette[colorIndex]
      };
    });
    
    return colorMap;
  }, [categoryDistribution]);

  // Chart data with improved aesthetics
  const pieChartData = {
    labels: Object.keys(categoryDistribution),
    datasets: [
      {
        label: "Category Distribution",
        data: Object.values(categoryDistribution),
        backgroundColor: Object.keys(categoryDistribution).map(category => 
          getCategoryColors[category]?.solid || COLORS.primary.blue
        ),
        borderColor: "rgba(255, 255, 255, 0.8)",
        borderWidth: 2,
        hoverOffset: 15
      },
    ],
  };

  const barChartData = {
    labels: Object.keys(priceRanges),
    datasets: [
      {
        label: "Price Distribution",
        data: Object.values(priceRanges),
        backgroundColor: [
          COLORS.transparent.green,
          COLORS.transparent.cyan,
          COLORS.transparent.blue,
          COLORS.transparent.purple,
          COLORS.transparent.pink
        ],
        borderColor: [
          COLORS.primary.green,
          COLORS.primary.cyan,
          COLORS.primary.blue,
          COLORS.primary.purple,
          COLORS.primary.pink
        ],
        borderWidth: 2,
        borderRadius: 6,
        hoverBackgroundColor: [
          COLORS.primary.green,
          COLORS.primary.cyan,
          COLORS.primary.blue,
          COLORS.primary.purple,
          COLORS.primary.pink
        ]
      },
    ],
  };

  const lineChartData = {
    labels: priceByCategory.map(item => item.category),
    datasets: [
      {
        label: "Average Price by Category",
        data: priceByCategory.map(item => item.avgPrice),
        borderColor: COLORS.primary.blue,
        backgroundColor: COLORS.transparent.blue,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: COLORS.primary.blue,
        pointBorderColor: '#fff',
        pointRadius: 6,
        pointHoverRadius: 8
      },
      {
        label: "Build Count by Category",
        data: priceByCategory.map(item => item.count * 10000), // Scaling for visibility
        borderColor: COLORS.primary.purple,
        backgroundColor: COLORS.transparent.purple,
        fill: true,
        tension: 0.4,
        yAxisID: 'y1',
        pointBackgroundColor: COLORS.primary.purple,
        pointBorderColor: '#fff',
        pointRadius: 6,
        pointHoverRadius: 8
      },
    ],
  };

  // Most used processors
  const topProcessors = Object.entries(componentUsage.processor || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const topGpus = Object.entries(componentUsage.gpu || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const radarData = {
    labels: componentComparison.map(item => item.category),
    datasets: [
      {
        label: "Average Price (scaled 1:10000)",
        data: componentComparison.map(item => item.avgPrice / 10000),
        backgroundColor: COLORS.transparent.cyan,
        borderColor: COLORS.primary.cyan,
        pointBackgroundColor: COLORS.primary.cyan,
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: COLORS.primary.cyan,
        pointRadius: 5,
        pointHoverRadius: 7
      },
      {
        label: "Build Count",
        data: componentComparison.map(item => item.count),
        backgroundColor: COLORS.transparent.purple,
        borderColor: COLORS.primary.purple,
        pointBackgroundColor: COLORS.primary.purple,
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: COLORS.primary.purple,
        pointRadius: 5,
        pointHoverRadius: 7
      },
    ],
  };

  // Enhanced PDF generation with branded styling
  const handleGenerateReport = async () => {
    console.log('📄 Generating refined PDF report...');
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  
    // ——————————————————————————————————————————————
    // Settings
    // ——————————————————————————————————————————————
    const COLORS = {
      primary:   '#0f172a', // slate-900 (professional dark)
      accent:    '#0ea5e9', // sky-400 (light blue accent)
      lightBg:   '#f9fafb', // gray-50
      bodyText:  '#334155', // slate-700
      footerText:'#94a3b8', // slate-400
    };
    const MARGIN = 15;
    const PAGE_WIDTH = 210;
    const PAGE_HEIGHT = 297;
  
    // ——————————————————————————————————————————————
    // Helpers
    // ——————————————————————————————————————————————
    const addHeader = () => {
      doc.setFillColor(COLORS.primary).rect(0, 0, PAGE_WIDTH, 20, 'F');
      doc.setFont('helvetica', 'bold').setFontSize(14).setTextColor('#ffffff')
        .text('Alpha IT Solutions -  Confidential', MARGIN, 13);
      doc.setFont('helvetica', 'normal').setFontSize(10).setTextColor('#cbd5e1')
        .text('26/C/3 Biyagama Road, Talwatta, Kelaniya, Sri Lanka', PAGE_WIDTH - MARGIN, 13, { align: 'right' });
    };
  
    const addFooter = () => {
      doc.setDrawColor(COLORS.footerText);
      doc.line(MARGIN, PAGE_HEIGHT - 15, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 15);
      doc.setFont('helvetica', 'normal').setFontSize(8).setTextColor(COLORS.footerText);
      doc.text('Generated by Alpha IT Solutions | Confidential', MARGIN, PAGE_HEIGHT - 8);
      const pageCount = doc.internal.getNumberOfPages();
      doc.text(`Page ${doc.internal.getCurrentPageInfo().pageNumber} of ${pageCount}`, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 8, { align: 'right' });
    };
  
    const addTitle = (text) => {
      doc.setFillColor(COLORS.lightBg).rect(0, 25, PAGE_WIDTH, 20, 'F');
      doc.setFont('helvetica', 'bold').setFontSize(20).setTextColor(COLORS.primary)
        .text(text, PAGE_WIDTH / 2, 38, { align: 'center' });
      doc.setFont('helvetica', 'normal').setFontSize(10).setTextColor(COLORS.bodyText)
        .text(`Date: ${new Date().toLocaleDateString()}`, MARGIN, 50);
    };
  
    const captureChart = async (ref, posY) => {
      if (!ref.current) return;
      const canvasEl = ref.current.querySelector('canvas');
      const canvas = await html2canvas(canvasEl, {
        backgroundColor: '#ffffff',
        scale: 2, // Higher quality
        useCORS: true
      });
      const imgData = canvas.toDataURL('image/png');
      const imgProps = doc.getImageProperties(imgData);
      const imgWidth = PAGE_WIDTH - 2 * MARGIN;
      const imgHeight = (imgProps.height * imgWidth) / imgProps.width;
      doc.addImage(imgData, 'PNG', MARGIN, posY, imgWidth, imgHeight);
      return posY + imgHeight + 10; // Return new Y position
    };
  
    const addSectionTitle = (text, y) => {
      doc.setFont('helvetica', 'bold').setFontSize(14).setTextColor(COLORS.accent);
      doc.text(text, MARGIN, y);
      return y + 8;
    };
  
    const addTable = (header, body, startY) => {
      doc.autoTable({
        startY: startY,
        head: [header],
        body: body,
        theme: 'striped',
        headStyles: {
          fillColor: COLORS.accent,
          textColor: '#ffffff',
          fontStyle: 'bold',
        },
        alternateRowStyles: {
          fillColor: COLORS.lightBg,
        },
        margin: { left: MARGIN, right: MARGIN },
        styles: { fontSize: 10, textColor: COLORS.bodyText },
      });
      return doc.lastAutoTable.finalY + 10;
    };
  
    // ——————————————————————————————————————————————
    // Document Build
    // ——————————————————————————————————————————————
    addHeader();
    addTitle('Pre-Built PC Analytics Report');
    let currentY = 60;
  
    console.log('💾 Capturing and adding charts...');
    
    currentY = addSectionTitle('Pie Chart: Category Distribution', currentY);
    currentY = await captureChart(pieRef, currentY) || currentY;
    
    doc.addPage();
    addHeader();
    currentY = 30;
  
    currentY = addSectionTitle('Bar Chart: Sales Distribution', currentY);
    currentY = await captureChart(barRef, currentY) || currentY;
  
    doc.addPage();
    addHeader();
    currentY = 30;
  
    currentY = addSectionTitle('Line Chart: Monthly Growth', currentY);
    currentY = await captureChart(lineRef, currentY) || currentY;
  
    doc.addPage();
    addHeader();
    currentY = 30;
  
    currentY = addSectionTitle('Radar Chart: Build Metrics', currentY);
    currentY = await captureChart(radarRef, currentY) || currentY;
  
    doc.addPage();
    addHeader();
    currentY = 30;
  
    doc.setFont('helvetica', 'bold').setFontSize(18).setTextColor(COLORS.primary)
      .text('Summary Tables', PAGE_WIDTH / 2, currentY, { align: 'center' });
    currentY += 10;
  
    // Category Table
    const categoryRows = Object.entries(categoryDistribution)
      .sort(([, a], [, b]) => b - a)
      .map(([cat, count]) => [cat, count, `${((count / builds.length) * 100).toFixed(1)}%`]);
    currentY = addSectionTitle('Category Distribution', currentY);
    currentY = addTable(['Category', 'Count', 'Percentage'], categoryRows, currentY);
  
    // Price Table
    const priceRows = Object.entries(priceRanges)
      .map(([range, count]) => [range, count, `${((count / builds.length) * 100).toFixed(1)}%`]);
    currentY = addSectionTitle('Price Range Distribution', currentY);
    currentY = addTable(['Price Range (LKR)', 'Count', 'Percentage'], priceRows, currentY);
  
    addFooter();
  
    console.log('✅ Refined PDF report generated!');
    const filename = `AlphaIT_PreBuild_Analytics_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(filename);
  };
  

  // Loading screen with branded styling
  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <div className="text-center">
        <div className="w-16 h-16 border-t-4 border-r-4 border-blue-500 border-solid rounded-full animate-spin mb-4 mx-auto"></div>
        <div className="relative mb-2">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 blur-xl opacity-25"></div>
          <p className="relative text-cyan-400 text-xl font-bold">LOADING ANALYTICS...</p>
        </div>
        <p className="text-gray-400">Preparing your dashboard</p>
      </div>
    </div>
  );

  // Error screen with enhanced styling
  if (error) return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <div className="text-center bg-gray-800/40 backdrop-blur-sm border border-red-500/50 p-8 rounded-lg shadow-2xl max-w-md">
        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
          <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="relative mb-2">
          <div className="absolute inset-0 bg-gradient-to-r from-red-600 to-orange-600 blur-xl opacity-25"></div>
          <p className="relative text-red-500 text-xl font-bold">SYSTEM ERROR</p>
        </div>
        <p className="text-gray-300 mt-4">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-6 px-4 py-2 bg-gradient-to-r from-red-600 to-orange-600 text-white font-bold rounded-lg shadow-lg text-sm transition-all duration-300 hover:shadow-red-500/30"
        >
          Retry
        </button>
      </div>
    </div>
  );

  // No data screen with enhanced styling
  if (builds.length === 0) return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <div className="text-center bg-gray-800/40 backdrop-blur-sm border border-cyan-500/50 p-8 rounded-lg shadow-2xl max-w-md">
        <div className="w-16 h-16 rounded-full bg-cyan-500/10 flex items-center justify-center mx-auto mb-4">
          <svg className="w-10 h-10 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        </div>
        <div className="relative mb-2">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 to-blue-600 blur-xl opacity-25"></div>
          <p className="relative text-cyan-400 text-xl font-bold">NO BUILDS FOUND</p>
        </div>
        <p className="text-gray-300 mt-4">Create some builds to see analytics.</p>
        <button 
          onClick={() => window.location.href = '/prebuilds/create'}
          className="mt-6 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-bold rounded-lg shadow-lg text-sm transition-all duration-300 hover:shadow-cyan-500/30"
        >
          Create New Build
        </button>
      </div>
    </div>
  );
  return (
    <div className="p-6 md:p-8 lg:p-10 bg-gray-900 min-h-screen text-white w-auto bg-fixed bg-opacity-10" style={{ backgroundImage: "url('/images/circuit-bg.png')" }}>
      {/* Header with enhanced gradient and glow effect */}
      <div className="relative mb-12">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 blur-xl opacity-25"></div>
        <div className="relative">
          <h2 className="text-4xl md:text-5xl font-bold py-6 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">
            PREBUILD ANALYTICS DASHBOARD
          </h2>
          <div className="h-1.5 w-3/4 md:w-2/3 lg:w-1/2 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-full"></div>
        </div>
      </div>
      
      {/* Generate Report Button with improved hover effects */}
      <div className="flex justify-center mb-16">
        <button
          onClick={handleGenerateReport}
          className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-lg shadow-lg text-lg transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-blue-500/30 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50"
        >
          <span className="flex items-center gap-2">
            <span>📄</span>
            <span>Generate Complete Analytics Report</span>
          </span>
        </button>
      </div>
      
      {/* Dashboard Grid with improved spacing and responsiveness */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10">
        {/* Category Distribution Pie Chart */}
        <div ref={pieRef} className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-cyan-900/20 hover:shadow-lg">
          <h3 className="text-2xl font-bold mb-8 text-cyan-400 text-center">Category Distribution</h3>
          <div className="bg-white/90 rounded-lg p-4 md:p-6 shadow-inner">
            <Pie
              data={pieChartData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: {
                      padding: 20,
                      font: {
                        size: 12
                      }
                    }
                  },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        const label = context.label || '';
                        const value = context.raw || 0;
                        const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return `${label}: ${value} (${percentage}%)`;
                      }
                    }
                  }
                }
              }}
            />
          </div>
        </div>
        
        {/* Price Distribution Bar Chart */}
        <div ref={barRef} className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-cyan-900/20 hover:shadow-lg">
          <h3 className="text-2xl font-bold mb-8 text-cyan-400 text-center">Price Distribution</h3>
          <div className="bg-white/90 rounded-lg p-4 md:p-6 shadow-inner">
            <Bar
              data={barChartData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                  legend: {
                    position: 'top',
                    labels: {
                      padding: 15,
                      font: {
                        size: 12
                      }
                    }
                  },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        return `Count: ${context.raw}`;
                      }
                    }
                  }
                }
              }}
            />
          </div>
        </div>
        
        {/* Price vs Count by Category Line Chart - Full width */}
        <div ref={lineRef} className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl lg:col-span-2 transition-transform duration-300 hover:shadow-cyan-900/20 hover:shadow-lg">
          <h3 className="text-2xl font-bold mb-8 text-cyan-400 text-center">Average Price & Count by Category</h3>
          <div className="bg-white/90 rounded-lg p-4 md:p-6 shadow-inner">
            <Line
              data={lineChartData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                  legend: {
                    position: 'top',
                    labels: {
                      padding: 15,
                      font: {
                        size: 12
                      }
                    }
                  },
                },
                scales: {
                  y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                      display: true,
                      text: 'Average Price (LKR)',
                      padding: {
                        bottom: 10
                      },
                      font: {
                        size: 12,
                        weight: 'bold'
                      }
                    }
                  },
                  y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                      display: true,
                      text: 'Build Count (scaled)',
                      padding: {
                        bottom: 10
                      },
                      font: {
                        size: 12,
                        weight: 'bold'
                      }
                    },
                    grid: {
                      drawOnChartArea: false,
                    },
                  },
                }
              }}
            />
          </div>
        </div>
        
        {/* Radar Chart for Category Comparison */}
        <div ref={radarRef} className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-cyan-900/20 hover:shadow-lg">
          <h3 className="text-2xl font-bold mb-8 text-cyan-400 text-center">Category Comparison</h3>
          <div className="bg-white/90 rounded-lg p-4 md:p-6 shadow-inner">
            <Radar
              data={radarData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                  legend: {
                    position: 'top',
                    labels: {
                      padding: 15,
                      font: {
                        size: 12
                      }
                    }
                  }
                },
                scales: {
                  r: {
                    angleLines: {
                      display: true,
                      color: 'rgba(0, 0, 0, 0.1)'
                    },
                    grid: {
                      color: 'rgba(0, 0, 0, 0.1)'
                    },
                    suggestedMin: 0,
                    ticks: {
                      backdropColor: 'transparent'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
        
        {/* Top 5 Most Expensive Builds - Enhanced table styling */}
        <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-cyan-900/20 hover:shadow-lg">
          <h3 className="text-2xl font-bold mb-8 text-cyan-400 text-center">Top 5 Most Expensive Builds</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-gray-700/50">
                  <th className="p-4 rounded-tl-lg font-semibold text-gray-300">Category</th>
                  <th className="p-4 font-semibold text-gray-300">Price</th>
                  <th className="p-4 font-semibold text-gray-300">Processor</th>
                  <th className="p-4 rounded-tr-lg font-semibold text-gray-300">GPU</th>
                </tr>
              </thead>
              <tbody>
                {topBuilds.map((build, index) => (
                  <tr 
                    key={index} 
                    className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${index === topBuilds.length - 1 ? 'rounded-b-lg' : ''}`}
                  >
                    <td className="p-4">
                      <span className="px-3 py-1 bg-blue-900/50 text-blue-300 rounded-full font-medium inline-block">
                        {build.category}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-lime-400 font-bold">
                      LKR {build.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                    </td>
                    <td className="p-4 text-gray-300">{build.processor}</td>
                    <td className="p-4 text-gray-300">{build.gpu}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      {/* Component Analysis Section with improved spacing */}
      <div className="mt-20">
        <div className="relative mb-12">
          <div className="absolute inset-0 bg-gradient-to-r from-green-600 to-blue-600 blur-xl opacity-25"></div>
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold py-4 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500">
              COMPONENT USAGE ANALYSIS
            </h2>
            <div className="h-1.5 w-1/2 md:w-2/5 bg-gradient-to-r from-green-400 to-blue-500 rounded-full"></div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
          {/* Processor Usage */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-green-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-6 text-green-400 text-center">Top 5 Most Used Processors</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-700/50">
                    <th className="p-3 md:p-4 rounded-tl-lg font-semibold text-gray-300">Processor</th>
                    <th className="p-3 md:p-4 rounded-tr-lg font-semibold text-gray-300 text-right">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {topProcessors.map(([processor, count], index) => (
                    <tr 
                      key={index} 
                      className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${index === topProcessors.length - 1 ? 'border-b-0' : ''}`}
                    >
                      <td className="p-3 md:p-4 text-gray-300">{processor}</td>
                      <td className="p-3 md:p-4 font-mono text-green-400 font-bold text-right">{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* GPU Usage */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-blue-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-6 text-blue-400 text-center">Top 5 Most Used GPUs</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-700/50">
                    <th className="p-3 md:p-4 rounded-tl-lg font-semibold text-gray-300">GPU</th>
                    <th className="p-3 md:p-4 rounded-tr-lg font-semibold text-gray-300 text-right">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {topGpus.map(([gpu, count], index) => (
                    <tr 
                      key={index} 
                      className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${index === topGpus.length - 1 ? 'border-b-0' : ''}`}
                    >
                      <td className="p-3 md:p-4 text-gray-300">{gpu}</td>
                      <td className="p-3 md:p-4 font-mono text-blue-400 font-bold text-right">{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* RAM Usage */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-purple-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-6 text-purple-400 text-center">Top RAM Configurations</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-700/50">
                    <th className="p-3 md:p-4 rounded-tl-lg font-semibold text-gray-300">RAM</th>
                    <th className="p-3 md:p-4 rounded-tr-lg font-semibold text-gray-300 text-right">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(componentUsage.ram || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([ram, count], index, arr) => (
                      <tr 
                        key={index} 
                        className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${index === arr.length - 1 ? 'border-b-0' : ''}`}
                      >
                        <td className="p-3 md:p-4 text-gray-300">{ram}</td>
                        <td className="p-3 md:p-4 font-mono text-purple-400 font-bold text-right">{count}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Storage Usage */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-orange-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-6 text-orange-400 text-center">Top Storage Solutions</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-700/50">
                    <th className="p-3 md:p-4 rounded-tl-lg font-semibold text-gray-300">Storage</th>
                    <th className="p-3 md:p-4 rounded-tr-lg font-semibold text-gray-300 text-right">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(componentUsage.storage || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([storage, count], index, arr) => (
                      <tr 
                        key={index} 
                        className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${index === arr.length - 1 ? 'border-b-0' : ''}`}
                      >
                        <td className="p-3 md:p-4 text-gray-300">{storage}</td>
                        <td className="p-3 md:p-4 font-mono text-orange-400 font-bold text-right">{count}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Power Supply Usage */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-yellow-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-6 text-yellow-400 text-center">Top Power Supply Units</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-700/50">
                    <th className="p-3 md:p-4 rounded-tl-lg font-semibold text-gray-300">Power Supply</th>
                    <th className="p-3 md:p-4 rounded-tr-lg font-semibold text-gray-300 text-right">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(componentUsage.powerSupply || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([psu, count], index, arr) => (
                      <tr 
                        key={index} 
                        className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${index === arr.length - 1 ? 'border-b-0' : ''}`}
                      >
                        <td className="p-3 md:p-4 text-gray-300">{psu}</td>
                        <td className="p-3 md:p-4 font-mono text-yellow-400 font-bold text-right">{count}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Case Usage */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 md:p-8 shadow-2xl transition-transform duration-300 hover:shadow-pink-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-6 text-pink-400 text-center">Top Case Choices</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-700/50">
                    <th className="p-3 md:p-4 rounded-tl-lg font-semibold text-gray-300">Case</th>
                    <th className="p-3 md:p-4 rounded-tr-lg font-semibold text-gray-300 text-right">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(componentUsage.casings || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([casing, count], index, arr) => (
                      <tr 
                        key={index} 
                        className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${index === arr.length - 1 ? 'border-b-0' : ''}`}
                      >
                        <td className="p-3 md:p-4 text-gray-300">{casing}</td>
                        <td className="p-3 md:p-4 font-mono text-pink-400 font-bold text-right">{count}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      
      {/* Performance Metrics Section with improved card styling */}
      <div className="mt-20">
        <div className="relative mb-12">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-red-600 blur-xl opacity-25"></div>
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold py-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-red-500">
              PERFORMANCE METRICS
            </h2>
            <div className="h-1.5 w-1/2 md:w-2/5 bg-gradient-to-r from-purple-400 to-red-500 rounded-full"></div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Total Builds - Enhanced card with subtle animation */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8 shadow-2xl flex flex-col items-center justify-center transform transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-gray-700/30">
            <h3 className="text-xl font-bold mb-4 text-gray-400">Total Builds</h3>
            <div className="text-5xl md:text-6xl font-bold text-white mb-4">{builds.length}</div>
            <p className="text-gray-400 text-sm">Across all categories</p>
          </div>
          
          {/* Average Price - Enhanced card with subtle animation */}
            <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8 shadow-2xl flex flex-col items-center justify-center transform transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-lime-900/20">
            <h3 className="text-xl font-bold mb-4 text-gray-400">Average Price</h3>
            
            <div className="flex flex-col items-center text-lime-400 mb-4">
                <span className="text-4xl md:text-5 xl font-bold">LKR</span> {/* LKR centered */}
                <span className="text-5xl md:text-6xl font-bold">
                {builds.length > 0 
                    ? (builds.reduce((sum, build) => sum + build.price, 0) / builds.length).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                    : "0.00"}
                </span>
            </div>

            <p className="text-gray-400 text-sm">Per build</p>
            </div>

          
          {/* Total Categories - Enhanced card with subtle animation */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8 shadow-2xl flex flex-col items-center justify-center transform transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-cyan-900/20">
            <h3 className="text-xl font-bold mb-4 text-gray-400">Total Categories</h3>
            <div className="text-5xl md:text-6xl font-bold text-cyan-400 mb-4">{Object.keys(categoryDistribution).length}</div>
            <p className="text-gray-400 text-sm">Different build types</p>
          </div>
        </div>
      </div>
      
      {/* Most Popular Components Section */}
      <div className="mt-20">
        <div className="relative mb-12">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-blue-600 blur-xl opacity-25"></div>
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold py-4 text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-blue-500">
              MOST POPULAR COMPONENTS
            </h2>
            <div className="h-1.5 w-1/2 md:w-2/5 bg-gradient-to-r from-emerald-400 to-blue-500 rounded-full"></div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Most Used Processor */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8 shadow-2xl transition-all duration-300 hover:shadow-emerald-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-8 text-emerald-400 text-center">Most Popular Processor</h3>
            {topProcessors.length > 0 ? (
              <div className="flex flex-col items-center">
                <div className="text-3xl md:text-4xl font-bold mb-6 text-white text-center">{topProcessors[0][0]}</div>
                <div className="text-xl md:text-2xl font-bold text-emerald-400 mb-2">Used in {topProcessors[0][1]} builds</div>
                <div className="text-gray-400 mt-2 text-center">
                  {((topProcessors[0][1] / builds.length) * 100).toFixed(1)}% of all builds
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-400">No processor data available</div>
            )}
          </div>
          
          {/* Most Used GPU */}
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8 shadow-2xl transition-all duration-300 hover:shadow-blue-900/20 hover:shadow-lg">
            <h3 className="text-2xl font-bold mb-8 text-blue-400 text-center">Most Popular GPU</h3>
            {topGpus.length > 0 ? (
              <div className="flex flex-col items-center">
                <div className="text-3xl md:text-4xl font-bold mb-6 text-white text-center">{topGpus[0][0]}</div>
                <div className="text-xl md:text-2xl font-bold text-blue-400 mb-2">Used in {topGpus[0][1]} builds</div>
                <div className="text-gray-400 mt-2 text-center">
                  {((topGpus[0][1] / builds.length) * 100).toFixed(1)}% of all builds
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-400">No GPU data available</div>
            )}
          </div>
        </div>
      </div>
      <div className="mt-20 mb-6 text-center">
              {/* Generate Report Button with improved hover effects */}
      <div className="flex justify-center mb-16">
        <button
          onClick={handleGenerateReport}
          className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-lg shadow-lg text-lg transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-blue-500/30 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50"
        >
          <span className="flex items-center gap-2">
            <span>📄</span>
            <span>Generate Complete Analytics Report</span>
          </span>
        </button>
      </div>
      </div>
      
      
      {/* Footer with subtle glow */}
      <div className="mt-20 mb-6 text-center">
        <div className="relative py-6">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 blur-xl opacity-20 rounded-lg"></div>
          <div className="relative">
            <p className="text-gray-400">© {new Date().getFullYear()} Alpha IT Solutions. All rights reserved.</p>
            <p className="mt-2 text-sm text-gray-500">Last updated: {new Date().toLocaleDateString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreBuildAnalytics;
          