import React, { useState, useEffect } from "react";

const CreateCustomPreBuild = () => {
  // General build info
  const [image, setImage] = useState("");
  const [buildCategory, setBuildCategory] = useState("Gaming"); 
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: "", type: "" });

  // Additional admin price field for the build
  const [additionalPrice, setAdditionalPrice] = useState(0);

  // Component options states
  const [processorOptions, setProcessorOptions] = useState([]);
  const [gpuOptions, setGpuOptions] = useState([]);
  const [ramOptions, setRamOptions] = useState([]);
  const [storageOptions, setStorageOptions] = useState([]);
  const [powerSupplyOptions, setPowerSupplyOptions] = useState([]);
  const [casingsOptions, setCasingsOptions] = useState([]);

  // Selected product for each component (store product object)
  const [selectedProcessor, setSelectedProcessor] = useState(null);
  const [selectedGpu, setSelectedGpu] = useState(null);
  const [selectedRam, setSelectedRam] = useState(null);
  const [selectedStorage, setSelectedStorage] = useState(null);
  const [selectedPowerSupply, setSelectedPowerSupply] = useState(null);
  const [selectedCasings, setSelectedCasings] = useState(null);

  // Compatibility options state for extra compatible products per category
  const [compatibility, setCompatibility] = useState({
    processor: [],
    gpu: [],
    ram: [],
    storage: [],
    powerSupply: [],
    casings: [],
  });

  // Calculate total price from selected components
  const componentsTotalPrice =
    (selectedProcessor?.price || 0) +
    (selectedGpu?.price || 0) +
    (selectedRam?.price || 0) +
    (selectedStorage?.price || 0) +
    (selectedPowerSupply?.price || 0) +
    (selectedCasings?.price || 0);

  // Final build price = components total + additional admin price
  const finalBuildPrice = componentsTotalPrice + Number(additionalPrice);

  // Helper function to fetch products by component category
  const fetchProductsByCategory = async (componentCategory, setOptions) => {
    try {
      const response = await fetch(`http://localhost:5000/api/products?category=${componentCategory}`);
      if (response.ok) {
        const data = await response.json();
        setOptions(data);
      } else {
        console.error(`Error fetching ${componentCategory} options`);
      }
    } catch (error) {
      console.error("Error fetching products:", error);
    }
  };

  // Fetch options for all components on mount
  useEffect(() => {
    fetchProductsByCategory("processor", setProcessorOptions);
    fetchProductsByCategory("gpu", setGpuOptions);
    fetchProductsByCategory("ram", setRamOptions);
    fetchProductsByCategory("storage", setStorageOptions);
    fetchProductsByCategory("powerSupply", setPowerSupplyOptions);
    fetchProductsByCategory("casings", setCasingsOptions);
  }, []);

  // Functions for handling compatibility options
  const addCompatibilityOption = (category) => {
    setCompatibility((prev) => ({
      ...prev,
      [category]: [...prev[category], null],
    }));
  };

  const handleCompatibilityChange = (category, index, productId) => {
    let options = [];
    switch (category) {
      case "processor":
        options = processorOptions;
        break;
      case "gpu":
        options = gpuOptions;
        break;
      case "ram":
        options = ramOptions;
        break;
      case "storage":
        options = storageOptions;
        break;
      case "powerSupply":
        options = powerSupplyOptions;
        break;
      case "casings":
        options = casingsOptions;
        break;
      default:
        break;
    }
    const selectedProduct = options.find((p) => p._id === productId) || null;
    setCompatibility((prev) => {
      const updated = { ...prev };
      updated[category][index] = selectedProduct;
      return updated;
    });
  };

  const removeCompatibilityOption = (category, index) => {
    setCompatibility((prev) => {
      const updated = { ...prev };
      updated[category] = updated[category].filter((_, i) => i !== index);
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation check: ensure each main component is selected
    if (
      !image ||
      !buildCategory ||
      !selectedProcessor ||
      !selectedGpu ||
      !selectedRam ||
      !selectedStorage ||
      !selectedPowerSupply ||
      !selectedCasings ||
      !description
    ) {
      showNotification("All fields are required!", "error");
      return;
    }

    setLoading(true);

    // Prepare compatibility data by extracting selected product IDs from each category
    const compatibilityData = {
      processor: compatibility.processor.filter((item) => item).map((item) => item._id),
      gpu: compatibility.gpu.filter((item) => item).map((item) => item._id),
      ram: compatibility.ram.filter((item) => item).map((item) => item._id),
      storage: compatibility.storage.filter((item) => item).map((item) => item._id),
      powerSupply: compatibility.powerSupply.filter((item) => item).map((item) => item._id),
      casings: compatibility.casings.filter((item) => item).map((item) => item._id),
    };

    // Prepare build data; note that price now includes the additional admin price.
    const preBuildData = {
      image,
      category: buildCategory,
      price: finalBuildPrice,
      processor: selectedProcessor._id,
      gpu: selectedGpu._id,
      ram: selectedRam._id,
      storage: selectedStorage._id,
      powerSupply: selectedPowerSupply._id,
      casings: selectedCasings._id,
      description,
      compatibility: compatibilityData,
    };

    try {
      const response = await fetch("http://localhost:5000/api/prebuilds/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(preBuildData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Server error!");
      }

      const data = await response.json();
      showNotification("Pre-build created successfully!", "success");
      console.log(data);

      // Reset form after successful submission
      resetForm();
    } catch (error) {
      console.error("Error:", error);
      showNotification("Error creating pre-build. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setImage("");
    setBuildCategory("Gaming");
    setDescription("");
    setAdditionalPrice(0);
    setSelectedProcessor(null);
    setSelectedGpu(null);
    setSelectedRam(null);
    setSelectedStorage(null);
    setSelectedPowerSupply(null);
    setSelectedCasings(null);
    setCompatibility({
      processor: [],
      gpu: [],
      ram: [],
      storage: [],
      powerSupply: [],
      casings: [],
    });
  };

  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(() => {
      setNotification({ show: false, message: "", type: "" });
    }, 3000);
  };

  return (
    <div className="max-w-4xl mx-auto p-8 bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl border border-gray-700">
      {/* Header with tech-inspired design */}
      <div className="mb-8 pb-6 border-b border-gray-700">
        <h2 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
          Create Custom PC Build
        </h2>
        <p className="text-gray-300 mt-3">Design your next-generation computing experience</p>
      </div>


      <form onSubmit={handleSubmit} className="space-y-8">
        {/* System Specifications section */}
       <div className="bg-gradient-to-r from-slate-900 to-slate-800 backdrop-blur-lg rounded-xl p-6 border border-cyan-800/50 shadow-[0_0_15px_rgba(6,182,212,0.15)] mt-8 relative overflow-hidden">
        <h3 className="text-lg font-medium text-gray-100 bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 mb-4 flex items-center">
          <span className="mr-2 relative"> System Specifications
          <span className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-cyan-400 to-blue-500"></span>
          </span>
        </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             {/* Image URL input */}
  <div className="space-y-2 group">
    <label className="block text-sm font-medium text-blue-400 group-hover:text-blue-300 transition-colors">
      Image URL
    </label>
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 text-blue-500 group-hover:text-blue-400 transition-colors"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
            clipRule="evenodd"
          />
        </svg>
      </div>
      <input
        type="text"
        value={image}
        onChange={(e) => setImage(e.target.value)}
        className="w-full pl-10 pr-4 py-3 bg-gray-900 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-blue-100 transition-all duration-300 placeholder-gray-500 hover:border-blue-600 shadow-sm"
        placeholder="https://example.com/image.jpg"
      />
      <div className="absolute inset-0 rounded-lg bg-blue-500/5 pointer-events-none"></div>
    </div>
  </div>

           {/* Build Category */}
  <div className="space-y-2 group">
    <label className="block text-sm font-medium text-blue-400 group-hover:text-blue-300 transition-colors">
      Build Category
    </label>
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 text-blue-500 group-hover:text-blue-400 transition-colors"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
        </svg>
      </div>
      <select
        value={buildCategory}
        onChange={(e) => setBuildCategory(e.target.value)}
        className="w-full pl-10 pr-10 py-3 bg-gray-900 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-blue-100 appearance-none transition-all duration-300 hover:border-blue-600 shadow-sm"
      >
        <option value="Gaming">Gaming</option>
        <option value="Budget">Budget</option>
        {/* Add other build types as needed */}
      </select>
      <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 text-blue-500 group-hover:text-blue-400 transition-colors"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </div>
      <div className="absolute inset-0 rounded-lg bg-blue-500/5 pointer-events-none"></div>
    </div>
  </div>

             {/* Additional Admin Price input */}
             <div className="space-y-2 group">
  <label className="block text-sm font-medium text-blue-400 group-hover:text-blue-300 transition-colors">
    Additional Price (Admin Preference)
  </label>
  <div className="relative">
    <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
      <span className="text-blue-500 font-medium">LKR </span>
    </div>
    <input
      type="number"
      value={additionalPrice}
      onChange={(e) => {
        const input = e.target.value;
        // Allow empty input
        if (input === "") {
          setAdditionalPrice("");
          return;
        }
        // Convert input to a number for validation
        const value = parseFloat(input);
        if (!isNaN(value) && value < 0) {
          // Optionally display an error notification
          toast.error("Negative value is not allowed");
          return;
        }
        setAdditionalPrice(input);
      }}
      className="w-full pl-12 pr-5 py-3 bg-gray-900 border border-gray-700 rounded-lg text-red-100 transition-all duration-300 hover:border-blue-600 shadow-sm"
      placeholder="0.00"
    />
    <div className="absolute inset-0 rounded-lg bg-blue-500/5 pointer-events-none"></div>
  </div>
</div>


   {/* Total Build Price (read-only, sum of component and additional price) */}
   <div className="space-y-2 group">
    <label className="block text-sm font-medium text-red-400 group-hover:text-blue-300 transition-colors">
      Total Build Price
    </label>
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
        <span className="text-red-500 font-medium">LKR </span>
      </div>
      <input
        type="number"
        value={finalBuildPrice.toFixed(2)}
        readOnly
        className="w-full pl-12 pr-5 py-3 bg-gray-900 border border-gray-700 rounded-lg text-red-500 shadow-inner transition-all duration-300 font-bold"
        placeholder="0.00"
      />
      <div className="absolute inset-0 rounded-lg bg-blue-500/10 pointer-events-none border border-red-500/30"></div>
    </div>
  </div>

  <div className="col-span-1 md:col-span-2">
    <div className="h-px bg-gradient-to-r from-transparent via-blue-600 to-transparent my-6 shadow-lg"></div>
  </div>

  {/* Dropdown for Processor */}
  <div className="space-y-3 group">
    <label className="block text-sm font-medium text-blue-400 group-hover:text-blue-300 transition-colors">
      <span className="flex items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 mr-2 text-blue-500 group-hover:text-blue-400 transition-all"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
            clipRule="evenodd"
          />
        </svg>
        PROCESSOR
      </span>
    </label>
    <select
      value={selectedProcessor?._id || ""}
      onChange={(e) => {
        const prod = processorOptions.find((p) => p._id === e.target.value);
        setSelectedProcessor(prod || null);
      }}
      className="w-full px-4 py-3 bg-gray-800/80 backdrop-blur-sm border-2 border-blue-900/50 hover:border-blue-700/70 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-500 text-blue-100 shadow-lg shadow-blue-900/20 transition-all duration-300 appearance-none"
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%234B91F7' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")", backgroundPosition: "right 0.75rem center", backgroundRepeat: "no-repeat", backgroundSize: "1.5em 1.5em", paddingRight: "2.5rem" }}
    >
      <option value="">Select a processor</option>
      {processorOptions.map((prod) => (
        <option key={prod._id} value={prod._id}>
          {prod.description} (LKR {prod.price})
        </option>
      ))}
    </select>
  </div>

  {/* Dropdown for GPU */}
  <div className="space-y-3 group">
    <label className="block text-sm font-medium text-green-400 group-hover:text-green-300 transition-colors">
      <span className="flex items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 mr-2 text-green-500 group-hover:text-green-400 transition-all"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M13 7H7v6h6V7z" />
          <path
            fillRule="evenodd"
            d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z"
            clipRule="evenodd"
          />
        </svg>
        GPU
      </span>
    </label>
    <select
      value={selectedGpu?._id || ""}
      onChange={(e) => {
        const prod = gpuOptions.find((p) => p._id === e.target.value);
        setSelectedGpu(prod || null);
      }}
      className="w-full px-4 py-3 bg-gray-800/80 backdrop-blur-sm border-2 border-green-900/50 hover:border-green-700/70 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-green-500 text-green-100 shadow-lg shadow-green-900/20 transition-all duration-300 appearance-none"
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2322C55E' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")", backgroundPosition: "right 0.75rem center", backgroundRepeat: "no-repeat", backgroundSize: "1.5em 1.5em", paddingRight: "2.5rem" }}
    >
      <option value="">Select a GPU</option>
      {gpuOptions.map((prod) => (
        <option key={prod._id} value={prod._id}>
          {prod.description} (LKR {prod.price})
        </option>
      ))}
    </select>
  </div>
  {/* Dropdown for RAM */}
  <div className="space-y-3 group">
    <label className="block text-sm font-medium text-purple-400 group-hover:text-purple-300 transition-colors">
      <span className="flex items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 mr-2 text-purple-500 group-hover:text-purple-400 transition-all"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
        </svg>
        RAM
      </span>
    </label>
    <select
      value={selectedRam?._id || ""}
      onChange={(e) => {
        const prod = ramOptions.find((p) => p._id === e.target.value);
        setSelectedRam(prod || null);
      }}
      className="w-full px-4 py-3 bg-gray-800/80 backdrop-blur-sm border-2 border-purple-900/50 hover:border-purple-700/70 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-purple-500 text-purple-100 shadow-lg shadow-purple-900/20 transition-all duration-300 appearance-none"
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23A855F7' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")", backgroundPosition: "right 0.75rem center", backgroundRepeat: "no-repeat", backgroundSize: "1.5em 1.5em", paddingRight: "2.5rem" }}
    >
      <option value="">Select RAM</option>
      {ramOptions.map((prod) => (
        <option key={prod._id} value={prod._id}>
          {prod.description} (LKR {prod.price})
        </option>
      ))}
    </select>
  </div>

            {/* Dropdown for Storage */}
  <div className="space-y-3 group">
    <label className="block text-sm font-medium text-yellow-400 group-hover:text-yellow-300 transition-colors">
      <span className="flex items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 mr-2 text-yellow-500 group-hover:text-yellow-400 transition-all"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5 4a3 3 0 00-3 3v10a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H5zm0 2h10a1 1 0 011 1v10a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1z"
            clipRule="evenodd"
          />
        </svg>
        STORAGE
      </span>
    </label>
    <select
      value={selectedStorage?._id || ""}
      onChange={(e) => {
        const prod = storageOptions.find((p) => p._id === e.target.value);
        setSelectedStorage(prod || null);
      }}
      className="w-full px-4 py-3 bg-gray-800/80 backdrop-blur-sm border-2 border-yellow-900/50 hover:border-yellow-700/70 rounded-lg focus:ring-2 focus:ring-yellow-600 focus:border-yellow-500 text-yellow-100 shadow-lg shadow-yellow-900/20 transition-all duration-300 appearance-none"
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23EAB308' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")", backgroundPosition: "right 0.75rem center", backgroundRepeat: "no-repeat", backgroundSize: "1.5em 1.5em", paddingRight: "2.5rem" }}
    >
      <option value="">Select Storage</option>
      {storageOptions.map((prod) => (
        <option key={prod._id} value={prod._id}>
          {prod.description} (LKR {prod.price})
        </option>
      ))}
    </select>
  </div>

            {/* Dropdown for Power Supply */}
  <div className="space-y-3 group">
    <label className="block text-sm font-medium text-red-400 group-hover:text-red-300 transition-colors">
      <span className="flex items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 mr-2 text-red-500 group-hover:text-red-400 transition-all"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
            clipRule="evenodd"
          />
        </svg>
        POWER SUPPLY
      </span>
    </label>
    <select
      value={selectedPowerSupply?._id || ""}
      onChange={(e) => {
        const prod = powerSupplyOptions.find((p) => p._id === e.target.value);
        setSelectedPowerSupply(prod || null);
      }}
      className="w-full px-4 py-3 bg-gray-800/80 backdrop-blur-sm border-2 border-red-900/50 hover:border-red-700/70 rounded-lg focus:ring-2 focus:ring-red-600 focus:border-red-500 text-red-100 shadow-lg shadow-red-900/20 transition-all duration-300 appearance-none"
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23EF4444' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")", backgroundPosition: "right 0.75rem center", backgroundRepeat: "no-repeat", backgroundSize: "1.5em 1.5em", paddingRight: "2.5rem" }}
    >
      <option value="">Select Power Supply</option>
      {powerSupplyOptions.map((prod) => (
        <option key={prod._id} value={prod._id}>
          {prod.description} (LKR {prod.price})
        </option>
      ))}
    </select>
  </div>


   {/* Dropdown for Casings */}
   <div className="space-y-3 group">
    <label className="block text-sm font-medium text-cyan-400 group-hover:text-cyan-300 transition-colors">
      <span className="flex items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 mr-2 text-cyan-500 group-hover:text-cyan-400 transition-all"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M3 5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V5zm2 0h10v10H5V5z"
            clipRule="evenodd"
          />
        </svg>
        CASE
      </span>
    </label>
    <select
      value={selectedCasings?._id || ""}
      onChange={(e) => {
        const prod = casingsOptions.find((p) => p._id === e.target.value);
        setSelectedCasings(prod || null);
      }}
      className="w-full px-4 py-3 bg-gray-800/80 backdrop-blur-sm border-2 border-cyan-900/50 hover:border-cyan-700/70 rounded-lg focus:ring-2 focus:ring-cyan-600 focus:border-cyan-500 text-cyan-100 shadow-lg shadow-cyan-900/20 transition-all duration-300 appearance-none"
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%234B91F7' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")", backgroundPosition: "right 0.75rem center", backgroundRepeat: "no-repeat", backgroundSize: "1.5em 1.5em", paddingRight: "2.5rem" }}
    >
      <option value="">Select Case</option>
      {casingsOptions.map((prod) => (
        <option key={prod._id} value={prod._id}>
          {prod.description} (LKR {prod.price})
        </option>
      ))}
    </select>
            </div>
          </div>
        </div>

        {/* Description section */}
<div className="bg-gradient-to-br from-gray-900 to-gray-800 backdrop-blur-sm rounded-xl p-6 border border-blue-500/30 shadow-lg relative overflow-hidden">
  {/* Decorative elements */}
  <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-xl"></div>
  <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-purple-500/10 rounded-full blur-xl"></div>
  
  {/* Header with glow effect */}
  
  <h3 className="text-lg font-medium text-gray-100 bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 mb-4 flex items-center">
    <span className="mr-2 relative">
      Build Name
      <span className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-cyan-400 to-blue-500"></span>
    </span>
  </h3>

  <div className="space-y-2">
    <label className="text-sm font-medium text-gray-100 flex items-center">
      <span className="mr-2">Enter Build Name</span>
      <span className="h-px w-16 bg-gradient-to-r from-blue-500/50 to-transparent"></span>
    </label>
    
    {/* Enhanced textarea with glow effect on focus */}
    <textarea
      value={description}
      onChange={(e) => setDescription(e.target.value)}
      className="w-full px-4 py-3 bg-gray-900/80 border border-gray-700 rounded-lg h-32 focus:ring-2 focus:ring-blue-500/70 focus:border-blue-500/70 text-gray-200 transition-all duration-300 shadow-[0_0_15px_rgba(59,130,246,0.1)] focus:shadow-[0_0_25px_rgba(59,130,246,0.2)]"
      placeholder="The Ultimate Gaming Rig."
    />
    
    <p className="text-xs text-gray-500 mt-1 italic">
      Provide a highlighting Build Name to Display on the Builds Page.
    </p>
  </div>
  
  {/* Decorative corner accent */}
  <div className="absolute top-0 right-0 w-6 h-6 overflow-hidden">
    <div className="absolute top-0 right-0 w-12 h-1 bg-blue-500/40 rotate-45 origin-bottom-left"></div>
  </div>
</div>

{/* Compatibility Options section */}
<div className="bg-gradient-to-r from-slate-900 to-slate-800 backdrop-blur-lg rounded-xl p-6 border border-cyan-800/50 shadow-[0_0_15px_rgba(6,182,212,0.15)] mt-8 relative overflow-hidden">
  {/* Tech pattern overlay */}
  <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGgtMTJ2MTJoMTJ6IiBzdHJva2U9InJnYmEoNiwxODIsMjEyLDAuMSkiIHN0cm9rZS13aWR0aD0iMSIvPjxwYXRoIGQ9Ik0xOCAwdjYwTTAgMThoNjBNMCAwdjYwTTAgMGg2ME02MCAwdjYwIiBzdHJva2U9InJnYmEoNiwxODIsMjEyLDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz48L2c+PC9zdmc+')] opacity-20"></div>
  
  <h3 className="text-xl font-medium text-cyan-400 mb-6 border-b border-cyan-700/50 pb-2 flex items-center">
    <span className="animate-pulse mr-2">›</span>
    <span className="uppercase tracking-wider">Compatibility Options</span>
    <span className="animate-pulse ml-2">‹</span>
  </h3>
  
  {["processor", "gpu", "ram", "storage", "powerSupply", "casings"].map((category) => (
    <div key={category} className="mb-6 backdrop-blur-sm bg-black/20 rounded-lg p-4 border-l-2 border-cyan-600/70 transform transition-all duration-300 hover:translate-x-1 hover:border-cyan-400">
      <h4 className="text-md font-medium text-cyan-300 capitalize mb-3 flex items-center">
        <span className="w-2 h-2 bg-cyan-400 rounded-full mr-2 animate-pulse"></span>
        {category}
      </h4>
      
      {compatibility[category].map((option, index) => (
        <div key={index} className="flex items-center space-x-2 mb-3">
          <select
            value={option?._id || ""}
            onChange={(e) => handleCompatibilityChange(category, index, e.target.value)}
            className="w-full px-4 py-2 bg-slate-900/90 border border-cyan-900 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-cyan-100 transition-all shadow-[0_0_10px_rgba(6,182,212,0.1)] outline-none appearance-none"
            style={{
              backgroundImage: "url('data:image/svg+xml;utf8,<svg fill=\"%2306b6d4\" height=\"24\" viewBox=\"0 0 24 24\" width=\"24\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M7 10l5 5 5-5z\"/></svg>')",
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 10px center"
            }}
          >
            <option value="" className="bg-slate-900 text-cyan-300">Select {category}</option>
            {(() => {
              let options = [];
              switch (category) {
                case "processor":
                  options = processorOptions;
                  break;
                case "gpu":
                  options = gpuOptions;
                  break;
                case "ram":
                  options = ramOptions;
                  break;
                case "storage":
                  options = storageOptions;
                  break;
                case "powerSupply":
                  options = powerSupplyOptions;
                  break;
                case "casings":
                  options = casingsOptions;
                  break;
                default:
                  break;
              }
              return options.map((prod) => (
                <option key={prod._id} value={prod._id} className="bg-slate-900 text-cyan-100">
                  {prod.description} (LKR {prod.price})
                </option>
              ));
            })()}
          </select>
          
          <button
            type="button"
            onClick={() => removeCompatibilityOption(category, index)}
            className="text-red-400 hover:text-red-300 transition-all duration-200 bg-red-900/20 p-2 rounded-lg hover:bg-red-900/40 hover:shadow-[0_0_10px_rgba(248,113,113,0.2)]"
            aria-label="Remove item"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      ))}
      
      <button
        type="button"
        onClick={() => addCompatibilityOption(category)}
        className="text-cyan-400 hover:text-cyan-300 transition-all duration-200 flex items-center space-x-1 bg-cyan-900/20 px-3 py-1.5 rounded-lg hover:bg-cyan-900/40 hover:shadow-[0_0_10px_rgba(6,182,212,0.2)]"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
        </svg>
        <span>Add {category} compatibility option</span>
      </button>
    </div>
  ))}
</div>

      {/* Notification component */}
      {notification.show && (
        <div
          className={`mb-6 p-4 rounded-xl flex items-center border ${
            notification.type === "success"
              ? "bg-green-900/20 border-green-500 text-green-400"
              : "bg-red-900/20 border-red-500 text-red-400"
          }`}
        >
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
              notification.type === "success" ? "bg-green-500/20" : "bg-red-500/20"
            }`}
          >
            {notification.type === "success" ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>
          {notification.message}
        </div>
      )}

        {/* Action buttons */}
        <div className="flex items-center justify-end space-x-4 pt-4">
          <button
            type="button"
            onClick={resetForm}
            className="px-6 py-3 text-sm font-medium text-gray-300 bg-gray-800 rounded-lg hover:bg-red-500 border border-red-700 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-all"
          >
            Reset
          </button>
          <button
            type="submit"
            disabled={loading}
            className={`px-8 py-3 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all flex items-center ${
              loading ? "opacity-70 cursor-not-allowed" : ""
            }`}
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Processing...
              </>
            ) : (
              <>
                Create Build
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4 ml-2"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateCustomPreBuild;