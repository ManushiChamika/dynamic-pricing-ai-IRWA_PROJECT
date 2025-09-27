import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { useTheme } from "./ThemeContext";
import { FaSun, FaMoon } from "react-icons/fa";
import jsPDF from "jspdf";
import { useDispatch, useSelector } from "react-redux";

const BudgetBuildDetail = () => {
  const { id } = useParams();
  const { isDark, toggleTheme } = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Retrieve cart items from Redux store
  const cartItems = useSelector((state) => state.cart.cartItems) || [];

  const [build, setBuild] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // State for storing validation messages
  const [validationMessages, setValidationMessages] = useState([]);

  // Products lookup state for mapping product IDs to details
  const [productsLookup, setProductsLookup] = useState({});
  // Modal state for editing build details
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  // Compatibility options fetched based on the build's compatibility field
  const [compatibilityOptions, setCompatibilityOptions] = useState({
    processor: [],
    gpu: [],
    ram: [],
    storage: [],
    powerSupply: [],
    casings: [],
  });
  // Local state for the edited build. Initially, we use the fetched build data.
  const [editedBuild, setEditedBuild] = useState(null);
  // Local state for temporary messages (confirmation or warning)
  const [message, setMessage] = useState("");

    // *** NEW: Product-details modal state ***
    const [isProductModalOpen, setIsProductModalOpen] = useState(false);
    const [productDetails, setProductDetails] = useState(null);
    const [prodLoading, setProdLoading] = useState(false);
    const [prodError, setProdError] = useState(null);

  // Fetch build details and products lookup concurrently
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch build details (global prebuild data)
        const buildResponse = await axios.get(`http://localhost:5000/api/prebuilds/${id}`);
        const fetchedBuild = buildResponse.data.data || buildResponse.data;
        if (fetchedBuild) {
          setBuild(fetchedBuild);
          // Initialize editedBuild with the current build values for a user-specific copy.
          setEditedBuild({ ...fetchedBuild });
        } else {
          setError("No data found for this build.");
        }

        // Fetch all products and create a lookup by _id
        const productsResponse = await axios.get("http://localhost:5000/api/products");
        const lookup = {};
        productsResponse.data.forEach((product) => {
          lookup[product._id] = product;
        });
        setProductsLookup(lookup);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("Unable to load build details. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // When the edit modal opens, fetch compatibility options from the backend
  useEffect(() => {
    if (isEditModalOpen && build && build.compatibility) {
      axios
        .get(`http://localhost:5000/api/prebuilds/${id}/compatibility`)
        .then((response) => {
          setCompatibilityOptions(response.data.data);
        })
        .catch((err) => {
          console.error("Error fetching compatibility options:", err);
        });
    }
  }, [isEditModalOpen, build, id]);

  // Helper: Given a product id and options, return its price
  const getProductPrice = (id, options) => {
    const prod = options.find((p) => p._id === id);
    return prod ? Number(prod.price) : 0;
  };

  // Recalculate the total price based on current selections (user-specific)
  const recalcPrice = () => {
    if (!editedBuild || !compatibilityOptions) return;
    const total =
      getProductPrice(editedBuild.processor, compatibilityOptions.processor) +
      getProductPrice(editedBuild.gpu, compatibilityOptions.gpu) +
      getProductPrice(editedBuild.ram, compatibilityOptions.ram) +
      getProductPrice(editedBuild.storage, compatibilityOptions.storage) +
      getProductPrice(editedBuild.powerSupply, compatibilityOptions.powerSupply) +
      getProductPrice(editedBuild.casings, compatibilityOptions.casings);
    setEditedBuild((prev) => ({ ...prev, price: total }));
  };

  // Recalculate price whenever any selection changes
  useEffect(() => {
    if (editedBuild && compatibilityOptions) {
      recalcPrice();
    }
  }, [
    editedBuild?.processor,
    editedBuild?.gpu,
    editedBuild?.ram,
    editedBuild?.storage,
    editedBuild?.powerSupply,
    editedBuild?.casings,
    compatibilityOptions
  ]);

  // Handler to update editedBuild when a dropdown changes
  const handleEditChange = (field, selectedId) => {
    setEditedBuild((prev) => ({ ...prev, [field]: selectedId }));
  };
  
  // Save the changes from the edit modal locally (without updating the global prebuild)
  const handleSaveChanges = () => {
    setBuild(editedBuild);
    setIsEditModalOpen(false);
  };

  // Helper to format price as LKR
  const formatPrice = (price) => {
    return price
      ? price.toLocaleString("en-US", { style: "currency", currency: "LKR" })
      : "N/A";
  }; 

  // Handler for generating PDF report (order detail)
const handleDownloadPdf = () => {
  if (!build) return;
  const doc = new jsPDF();

  // Brand colors
  const primaryColor   = "#2c3e50"; // Dark blue
  const secondaryColor = "#7f8c8d"; // Gray
  const accentColor    = "#e74c3c"; // Red

  // Load logo, then draw rest in .then()
  const logoUrl = `${window.location.origin}/Logo.jpg`;
  new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.onload = () => {
      const logoW = 35;
      const logoH = logoW * (img.height / img.width);
      doc.addImage(img, "JPEG", 15, 15, logoW, logoH);
      resolve();
    };
    img.onerror = reject;
    img.src = logoUrl;
  })
    .then(() => {
      // Company info (top-right)
      doc.setFont("helvetica");
      doc.setFontSize(10);
      doc.setTextColor(secondaryColor);
      ["Alpha IT Solutions",
       "26/C/3 Biyagama Road, Talwatta",
       "Gonawala, Kelaniya 11600",
       "Tel: 077 625 2822"]
        .forEach((line, i) =>
          doc.text(line, 180, 20 + i*5, { align: "right" })
        );

      // Title
      doc.setFontSize(16);
      doc.setTextColor(primaryColor);
      doc.setFont(undefined, "bold");
      doc.text("CUSTOM BUILD REPORT", 105, 60, { align: "center" });

      // Separator
      let y = 70;
      doc.setDrawColor(primaryColor);
      doc.setLineWidth(0.3);
      doc.line(15, y, 195, y);
      y += 10;

            // ─── Invoice Date (today) ────────────────────────────────────
            y += 3;
            const now        = new Date();
            const dateString = now.toLocaleDateString("en-US", {
              year:  "numeric",
              month: "long",
              day:   "numeric"
            });
            const timeString = now.toLocaleTimeString("en-US");
      
            doc.setFontSize(10).setTextColor(secondaryColor);
            doc.text("Invoice Date:", 15, y);
            doc.setFontSize(11).setTextColor(primaryColor);
            doc.text(`${dateString} ${timeString}`, 50, y);
            y += 15;      

      // Reference & Date
      doc.setFontSize(10);
      doc.setTextColor(secondaryColor);
      doc.text("Build Reference #:", 15, y);      

      doc.setFontSize(11);
      doc.setTextColor(primaryColor);
      doc.text(build._id, 50, y);

      // Status badge
      doc.setFillColor("#eef9ff");       // light accent
      doc.setDrawColor(accentColor);
      doc.roundedRect(160, y - 3, 30, 10, 2, 2, "FD");
      doc.setTextColor(accentColor);
      doc.setFontSize(9);
      doc.text(build.status?.toUpperCase() || "PENDING",
               175, y + 3, { align: "center" });
      y += 20;

      // Order Details section
      doc.setFontSize(14);
      doc.setTextColor(primaryColor);
      doc.setFont(undefined, "normal");
      doc.text("Order Details", 15, y);
      y += 8;

      const orderFields = [
        { label: "Category",    value: build.category },
        { label: "Build Name", value: build.description },
        { label: "Price",       value: formatPrice(build.price) }
      ];
      orderFields.forEach(f => {
        doc.setFontSize(10);
        doc.setTextColor(secondaryColor);
        doc.text(`${f.label}:`, 15, y);
        doc.setFontSize(11);
        doc.setTextColor(primaryColor);
        doc.text(f.value, 50, y);
        y += 7;
      });
      y += 10;

      // Specifications section
      doc.setFontSize(14);
      doc.setTextColor(primaryColor);
      doc.text("Specifications", 15, y);
      y += 8;

      const specFields = [
        { label: "Processor",    value: productsLookup[build.processor]?.description || build.processor },
        { label: "GPU",          value: productsLookup[build.gpu]?.description       || build.gpu },
        { label: "RAM",          value: productsLookup[build.ram]?.description       || build.ram },
        { label: "Storage",      value: productsLookup[build.storage]?.description   || build.storage },
        { label: "Power Supply", value: productsLookup[build.powerSupply]?.description || build.powerSupply },
        { label: "Casing",       value: productsLookup[build.casings]?.description    || build.casings }
      ];
      specFields.forEach(s => {
        doc.setFontSize(10);
        doc.setTextColor(secondaryColor);
        doc.text(`${s.label}:`, 15, y);
        doc.setFontSize(11);
        doc.setTextColor(primaryColor);
        doc.text(s.value, 50, y);
        y += 7;
      });
      y += 15;

      // Footer
      doc.setFontSize(8);
      doc.setTextColor(secondaryColor);
      doc.text(
        "Thank you for your order! For support, call 077 625 2822.",
        105, y, { align: "center" }
      );

      // Light border
      doc.setDrawColor("#F9FAFB");
      doc.setLineWidth(0.5);
      doc.rect(5, 5, 200, 287);

      // Save
      doc.save(`Alpha IT CustomBuild Report (Build_id-${build._id.slice(-8)}).pdf`);
    })
    .catch((err) => {
      console.error("PDF generation failed:", err);
      toast.error("Failed to download report. Please try again.");
    });
};


  if (loading)
    return <p className="text-center text-lg font-semibold">Loading...</p>;
  if (error)
    return <p className="text-red-500 text-center">{error}</p>;
  if (!build)
    return <p className="text-center text-red-500">Build not found.</p>;

  // Display specifications using productsLookup (for non-edit mode)
  const specs = [
    {
      id: "spec-processor",
      label: "Processor",
      value: productsLookup[build.processor]
        ? productsLookup[build.processor].description
        : build.processor,
    },
    {
      id: "spec-gpu",
      label: "GPU",
      value: productsLookup[build.gpu]
        ? productsLookup[build.gpu].description
        : build.gpu,
    },
    {
      id: "spec-ram",
      label: "RAM",
      value: productsLookup[build.ram]
        ? productsLookup[build.ram].description
        : build.ram,
    },
    {
      id: "spec-storage",
      label: "Storage",
      value: productsLookup[build.storage]
        ? productsLookup[build.storage].description
        : build.storage,
    },
    {
      id: "spec-powerSupply",
      label: "Power Supply",
      value: productsLookup[build.powerSupply]
        ? productsLookup[build.powerSupply].description
        : build.powerSupply,
    },
    {
      id: "spec-casings",
      label: "Casings",
      value: productsLookup[build.casings]
        ? productsLookup[build.casings].description
        : build.casings,
    },
  ];

  // Check if the current Budget build (prebuild) is already in the cart
  const isBudgetBuildInCart = () => {
    return cartItems.some((item) => item._id === build?._id);
  };

  const handleAddToCart = () => {
    if (isBudgetBuildInCart()) {
      setMessage("Build is already in cart. Adjust quantity in the shopping cart.");
      setTimeout(() => {
        navigate('/ShoppingCart');
        setMessage('');
      }, 2000);
      return;
    }
  
    // Destructure core fields
    const { _id, category, description, price, image } = build;
  
    // Build an array of specs for the cart item
    const specsForCart = [
      {id: build.processor,  label: 'Processor',    value: productsLookup[build.processor]?.description || build.processor },
      {id: build.gpu, label: 'GPU',          value: productsLookup[build.gpu]?.description       || build.gpu },
      {id: build.ram , label: 'RAM',          value: productsLookup[build.ram]?.description       || build.ram },
      {id: build.storage , label: 'Storage',      value: productsLookup[build.storage]?.description   || build.storage },
      {id: build.powerSupply, label: 'Power Supply', value: productsLookup[build.powerSupply]?.description || build.powerSupply },
      {id: build.casings ,  label: 'Casing',       value: productsLookup[build.casings]?.description    || build.casings },
    ];
  
    // Create a payload variable
    const payload = {
      _id,
      category,
      description,
      price,
      image,
      specs: specsForCart,
      quantity: 1,
    };
  
    // Log it so you can inspect in the console
    console.log("🛒 Dispatching ADD_TO_CART with payload:", payload);
  
    // Dispatch once, using the payload variable
    dispatch({ type: 'ADD_TO_CART', payload });
  
    setMessage("Build added to cart!");
    setTimeout(() => {
      navigate('/ShoppingCart');
      setMessage('');
    }, 2000);
  };

    // *** NEW: Fetch + show single product details ***
    const showProductDetails = async (prodId) => {
      // 1) open the modal immediately so we see loading state or error
      setIsProductModalOpen(true);
      setProdLoading(true);
      setProdError(null);
    
      try {
        // 2) try your in-memory lookup first
        const local = productsLookup[prodId];
        if (local) {
          setProductDetails(local);
        } else {
          // fallback: fetch from server
          const res = await axios.get(`http://localhost:5000/api/products/${prodId}`);
          const pd =
            res.data.data      ? res.data.data :
            res.data.product   ? res.data.product :
            Array.isArray(res.data) ? res.data[0] :
            res.data;
          setProductDetails(pd);
        }
      } catch (e) {
        console.error("❌ loading product:", e);
        setProdError("Could not load product details.");
      } finally {
        setProdLoading(false);
      }
    };
  


  return (
    <div className={`min-h-screen py-10 px-4 ${isDark ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-800"}`}>
      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 p-3 rounded-full bg-gray-800 text-white shadow-lg hover:bg-gray-700"
      >
        {isDark ? <FaSun className="text-yellow-500" /> : <FaMoon className="text-blue-400" />}
      </button>

      {/* Transient message */}
      {message && (
        <div className="fixed top-20 right-4 bg-green-600 text-white px-4 py-2 rounded animate-fadeIn z-50">
          {message}
        </div>
      )}

      {/* Main build card */}
      <div className={`max-w-6xl mx-auto p-6 rounded-lg shadow-lg flex flex-col md:flex-row gap-6 ${isDark ? "bg-gray-800" : "bg-white"}`}>
        {/* Image */}
        <div className="md:w-1/2">
          <img
            src={build.image || "https://via.placeholder.com/600"}
            alt={build.category}
            className="w-full h-auto rounded-lg shadow-md object-cover"
          />
        </div>

        {/* Details */}
        <div className="md:w-1/2 p-6 rounded-xl bg-gradient-to-br from-gray-900 to-gray-800 border border-purple-500/30 backdrop-blur-sm flex flex-col justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-600">
              {build.description}
            </h1>
            <p className="text-lg mb-4 text-cyan-300 font-mono">
              Build Type: {build.category}
            </p>

            {/* Price & Availability */}
            <div className="p-4 rounded-lg bg-black/40 border border-cyan-500/20 mb-6">
              <p className="text-2xl font-bold text-cyan-400">
                <span className="text-gray-400 text-base font-mono">PRICE:</span>{" "}
                {formatPrice(build.price)}
              </p>
              <p className="text-green-400 text-sm font-semibold mt-2 flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse inline-block" />
                AVAILABLE NOW
              </p>
            </div>

            {/* Specifications */}
            <div className="mt-6">
              <h2 className="text-xl font-semibold mb-3 text-cyan-300 font-mono uppercase tracking-wider flex items-center">
                <span className="w-1 h-6 bg-purple-500 mr-2 inline-block"></span>
                Specifications
              </h2>
              <div className="overflow-hidden rounded-lg border border-cyan-500/30 backdrop-blur-sm">
                <table className="w-full border-collapse">
                  <tbody>
                    {specs.map((spec, idx) => (
                      <tr
                        key={spec.id + idx}
                        className={`${idx % 2 === 0 ? "bg-black/20" : "bg-black/40"} border-b border-cyan-900/50 hover:bg-cyan-900/20 transition`}
                      >
                        <td className="p-3 font-mono text-cyan-400 text-sm">
                          {spec.label}
                        </td>
                        <td className="p-3 text-gray-300 font-medium flex items-center justify-between">
                          <span>{spec.value || "N/A"}</span>
                          {spec.id && (
                            <button
                              onClick={() => showProductDetails(spec.id)}
                              className="ml-4 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Details
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Action buttons */}
            <div className="mt-8 flex flex-col md:flex-row gap-4">
              <button
                onClick={handleAddToCart}
                disabled={isBudgetBuildInCart()}
                className={`px-6 py-2 rounded-lg text-white transition ${
                  isBudgetBuildInCart()
                    ? "bg-blue-600 opacity-50 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700"
                }`} > 🛒 Add to Cart </button>
              <button onClick={() => setIsEditModalOpen(true)}
                className="px-6 py-3 rounded-md bg-gradient-to-r from-purple-600 to-purple-700 text-white hover:from-purple-500 hover:to-purple-600 flex items-center gap-2 shadow-lg"
              > 🛠️ CUSTOMIZE BUILD </button>
              <button onClick={handleDownloadPdf}
                className="px-6 py-3 rounded-md bg-gradient-to-r from-green-700 to-green-800 text-white hover:from-emerald-600 hover:to-emerald-700 flex items-center gap-2 shadow-lg border border-cyan-500/30"
              > 📄 DOWNLOAD ORDER REPORT
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* No reviews placeholder */}
      <div className={`text-center p-8 italic border-2 border-dashed rounded-lg mt-8 ${
        isDark ? "border-gray-700 text-gray-400" : "border-gray-300 text-gray-500"
      }`}>
        <p>No reviews yet. Be the first to leave one!</p>
      </div>

      {/* ——— Customize Modal ——— */}
      {isEditModalOpen && editedBuild && (
        <div className="fixed inset-0 bg-opacity-75 bg-gradient-to-br from-purple-900 via-blue-800 to-purple-800 flex items-center justify-center z-50">
          <div className={`relative w-full max-w-lg rounded-lg shadow-2xl overflow-hidden ${isDark ? "bg-gray-900 text-white" : "bg-gray-800 text-gray-100"}`}>
            {/* Glowing borders */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-purple-600 opacity-30 rounded-lg"></div>
            <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg blur opacity-30 transition duration-1000 group-hover:opacity-50"></div>
            {/* Header */}
            <div className="relative bg-gradient-to-r from-gray-900 to-gray-800 p-4 border-b border-cyan-600">
              <div className="flex items-center">
                <span className="w-3 h-3 mr-2 rounded-full bg-red-500"></span>
                <span className="w-3 h-3 mr-2 rounded-full bg-yellow-500"></span>
                <span className="w-3 h-3 mr-4 rounded-full bg-green-500"></span>
                <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-500">
                  CUSTOMIZE YOUR BUILD
                </h2>
              </div>
            </div>
            {/* Content */}
            <div className="relative p-6 max-h-[70vh] overflow-y-auto">
              {[
                { field: "processor",    label: "PROCESSOR",    options: compatibilityOptions.processor,    icon: "⚡" },
                { field: "gpu",          label: "GRAPHICS",     options: compatibilityOptions.gpu,          icon: "🎮" },
                { field: "ram",          label: "RAM",          options: compatibilityOptions.ram,          icon: "💾" },
                { field: "storage",      label: "STORAGE",      options: compatibilityOptions.storage,      icon: "💿" },
                { field: "powerSupply",  label: "PSU",          options: compatibilityOptions.powerSupply,  icon: "⚡" },
                { field: "casings",      label: "CASING",       options: compatibilityOptions.casings,      icon: "🖥️" },
              ].map(({ field, label, options, icon }) => (
                <div key={field} className="mb-5 group">
                  <label className="flex items-center mb-2 font-bold text-sm tracking-wider text-cyan-400">
                    <span className="mr-2">{icon}</span>{label}
                  </label>
                  {options.length ? (
                    <div className="relative">
                      <select
                        value={editedBuild[field] || ""}
                        onChange={(e) => handleEditChange(field, e.target.value)}
                        className="w-full p-3 pr-10 pl-4 bg-gray-800 border border-gray-700 rounded text-gray-200 appearance-none focus:outline-none focus:ring-1 focus:ring-cyan-500 transition hover:border-cyan-400"
                      >
                        <option value="">{`Select ${label}`}</option>
                        {options.map((opt) => (
                          <option key={opt._id} value={opt._id}>
                            {opt.description} – (LKR {opt.price})
                          </option>
                        ))}
                      </select>
                      <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                        <svg className="w-5 h-5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                  ) : (
                    <p className="p-3 text-sm italic bg-gray-800 bg-opacity-50 rounded border border-red-900 text-red-400">
                      No components available
                    </p>
                  )}
                </div>
              ))}

              {/* Total Cost */}
              <div className="mb-6 group">
                <label className="flex items-center mb-2 font-bold text-sm tracking-wider text-cyan-400">
                  <span className="mr-2">💰</span>TOTAL COST
                </label>
                <div className="relative">
                  <input
                    readOnly
                    value={formatPrice(editedBuild.price)}
                    className="w-full p-3 pr-12 bg-gray-800 text-cyan-300 font-mono text-lg rounded border border-gray-700 focus:outline-none focus:ring-1 focus:ring-cyan-500 tracking-wider text-right"
                  />
                  <div className="absolute right-3 inset-y-0 flex items-center text-cyan-400 font-bold">
                    LKR
                  </div>
                </div>
              </div>
            </div>
            {/* Footer */}
            <div className="relative p-4 bg-gray-900 border-t border-gray-800 flex justify-end gap-4">
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="flex items-center px-5 py-2 bg-gray-800 text-gray-300 rounded hover:bg-gray-700 transition"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
                CANCEL
              </button>
              <button
                onClick={handleSaveChanges}
                className="flex items-center px-5 py-2 bg-gradient-to-r from-cyan-600 to-blue-700 text-white rounded shadow-lg hover:from-cyan-500 hover:to-blue-600 transition"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                SAVE BUILD
              </button>
            </div>
          </div>
        </div>
      )}


{/* ——— Hyper-Advanced Gaming Product Details Modal with Inline Styles ——— */}
{isProductModalOpen && (
  <div className="fixed inset-0 bg-black bg-opacity-95 backdrop-blur-xl flex items-center justify-center z-50 transition-all duration-500">
    <div className="relative bg-gradient-to-br from-gray-900 via-black to-gray-950 border-2 border-purple-600 rounded-xl shadow-2xl overflow-auto max-h-[90vh] w-11/12 md:w-4/5 lg:w-3/4 p-8 text-gray-100">
      {/* Neo-Cyberpunk Corner Elements with inline animation */}
      <div className="absolute top-0 left-0 w-16 h-16 border-t-2 border-l-2 border-cyan-400 rounded-tl-lg opacity-80"
        style={{animation: 'pulse 2s infinite'}}></div>
      <div className="absolute top-0 right-0 w-16 h-16 border-t-2 border-r-2 border-purple-500 rounded-tr-lg opacity-80"
        style={{animation: 'pulse 2s infinite', animationDelay: '0.2s'}}></div>
      <div className="absolute bottom-0 left-0 w-16 h-16 border-b-2 border-l-2 border-purple-500 rounded-bl-lg opacity-80"
        style={{animation: 'pulse 2s infinite', animationDelay: '0.4s'}}></div>
      <div className="absolute bottom-0 right-0 w-16 h-16 border-b-2 border-r-2 border-cyan-400 rounded-br-lg opacity-80"
        style={{animation: 'pulse 2s infinite', animationDelay: '0.6s'}}></div>
      
      {/* Digital Circuit Pattern Overlay */}
      <div className="absolute inset-0 opacity-5 pointer-events-none"
        style={{backgroundImage: 'url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNDB2NDBIMHoiLz48cGF0aCBkPSJNMCAwaDJ2Mkgwem00IDBoMnYySDB6bTQgMGgydjJIMHptNCAwaDJ2Mkgwem00IDBoMnYySDB6bTQgMGgydjJIMHptNCAwaDJ2Mkgwem00IDBoMnYySDB6bTQgMGgydjJIMHptNCAwaDJ2Mkgwek0yIDJoMnYySDBtNCAwaDJ2MkgwbTQgMGgydjJIMG00IDBoMnYySDBtNCAwaDJ2MkgwbTQgMGgydjJIMG00IDBoMnYySDBtNCAwaDJ2MkgwIiBmaWxsPSIjZmZmIi8+PC9nPjwvc3ZnPg==")'}}></div>
      
{/* Improved Hexagonal Close Button */}
<div className="absolute top-1 right-4">
  <button 
    onClick={() => setIsProductModalOpen(false)} 
    className="bg-gradient-to-br from-red-600 to-red-900 text-white w-12 h-12 flex items-center justify-center transition-all duration-300 hover:shadow-xl relative"
    style={{
      clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
    }}
    aria-label="Close product modal"
  >
    <span className="text-lg font-bold transition-colors duration-300 hover:text-red-200">✕</span>
    <div className="absolute inset-0 bg-transparent border-2 border-red-400 opacity-0 hover:opacity-100 transition-opacity duration-300"
      style={{
        clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
      }}
    ></div>
  </button>
</div>
      
      {/* Advanced Gaming Spinner with Neon Glow */}
      {prodLoading && (
        <div className="flex justify-center items-center h-80">
          <div className="relative w-32 h-32">
            <div className="rounded-full h-32 w-32 border-t-4 border-b-4 border-purple-600 opacity-75 shadow-lg shadow-purple-500/50"
              style={{animation: 'spin 1s linear infinite'}}></div>
            <div className="rounded-full h-32 w-32 border-r-4 border-l-4 border-cyan-400 absolute top-0 left-0 opacity-75 shadow-lg shadow-cyan-500/50"
              style={{animation: 'spin 1.5s linear infinite reverse'}}></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-cyan-400 font-bold text-xl tracking-widest"
              style={{animation: 'pulse 2s infinite'}}
            >LOADING</div>
            
            {/* Decorative spinner elements */}
            <div className="absolute top-0 left-0 right-0 bottom-0 border-4 border-dashed border-purple-500/20 rounded-full"></div>
            <div className="absolute top-4 left-4 right-4 bottom-4 border-4 border-dotted border-cyan-500/20 rounded-full"></div>
          </div>
        </div>
      )}
      
      {/* Glitch Error Message with inline styles */}
      {prodError && (
        <div className="bg-red-900/50 border-l-4 border-red-500 p-6 rounded-md my-6 shadow-lg shadow-red-500/40 relative overflow-hidden"
          style={{animation: 'pulse 2s infinite'}}>
          <p className="text-red-300 font-medium text-lg relative z-10">{prodError}</p>
          <div className="absolute top-0 left-0 w-full h-full bg-red-800/20"
            style={{
              animation: '0.3s infinite',
              animationName: 'glitchAnim',
            }}></div>
          <div className="absolute top-0 right-0 w-1 h-full bg-red-500"
            style={{animation: 'pulse 2s infinite'}}></div>
            
          {/* Add inline keyframes for glitch */}
          <style>
            {`
              @keyframes glitchAnim {
                0% { transform: translate(0) }
                20% { transform: translate(-2px, 2px) }
                40% { transform: translate(-2px, -2px) }
                60% { transform: translate(2px, 2px) }
                80% { transform: translate(2px, -2px) }
                100% { transform: translate(0) }
              }
            `}
          </style>
        </div>
      )}
      
      {!prodLoading && productDetails && (
        <>
          {/* Futuristic Title with inline animation */}
          <h2 className="text-4xl font-black mb-8 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-400 pb-4 tracking-wider uppercase relative"
            style={{
              backgroundSize: '200% 200%',
              animation: 'gradient 3s ease infinite'
            }}>
            {productDetails.description || "Component Details"}
            <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-600 via-cyan-400 to-purple-600 shadow-lg shadow-cyan-500/50"></div>
            <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-1/2 h-0.5 bg-white"
              style={{animation: 'pulse 2s infinite'}}></div>
            
            {/* Inline gradient animation */}
            <style>
              {`
                @keyframes gradient {
                  0% { background-position: 0% 50% }
                  50% { background-position: 100% 50% }
                  100% { background-position: 0% 50% }
                }
              `}
            </style>
          </h2>
          
          <div className="flex flex-col md:flex-row gap-8 mb-10">
            {/* Enhanced Image Section with 3D Effects */}
            <div className="md:w-1/2">
              <div className="relative overflow-hidden rounded-lg border-2 border-purple-600/80 shadow-xl shadow-purple-500/40 group"
                style={{perspective: '1000px'}}>
                <div className="transform transition-all duration-700 group-hover:scale-110 group-hover:rotate-1"
                  style={{transformStyle: 'preserve-3d'}}>
                  <img
                    src={productDetails.image}
                    alt={productDetails.description}
                    className="w-full h-auto object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-60 group-hover:opacity-40 transition-opacity duration-300"></div>
                </div>
                
                {/* RGB Gaming Light Effect */}
                <div className="absolute -bottom-2 left-0 right-0 h-3 bg-gradient-to-r from-red-500 via-green-500 to-blue-500 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300 shadow-lg shadow-cyan-500/50"
                  style={{
                    backgroundSize: '200% 200%',
                    animation: 'gradient 3s ease infinite'
                  }}></div>
                
                {/* Scan Line Effect */}
                <div className="absolute inset-0 opacity-10 pointer-events-none"
                  style={{
                    background: 'linear-gradient(transparent 50%, rgba(0, 0, 0, 0.5) 50%)',
                    backgroundSize: '100% 4px'
                  }}></div>
                
                {/* Glowing Border on Hover */}
                <div className="absolute inset-0 border-2 border-transparent group-hover:border-cyan-400/50 rounded-lg transition-all duration-300 group-hover:shadow-lg group-hover:shadow-cyan-500/30"></div>
              </div>
            </div>
            
            {/* Futuristic Info Panel with HUD Style */}
            <div className="md:w-1/2">
              <div className="bg-gray-900/80 backdrop-blur-lg p-8 rounded-lg border border-gray-700 shadow-inner relative overflow-hidden group hover:shadow-cyan-500/20 transition-all duration-300">
                {/* Tech HUD Elements */}
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 via-cyan-400 to-purple-500 shadow-lg shadow-purple-500/50"></div>
                <div className="absolute top-0 right-0 w-1 h-full bg-gradient-to-b from-purple-500 via-cyan-400 to-purple-500 shadow-lg shadow-cyan-500/50"></div>
                
                {/* Animated Digital Noise Background */}
                <div className="absolute inset-0 opacity-5"
                  style={{
                    backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.65\' numOctaves=\'3\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\'/%3E%3C/svg%3E")',
                    animation: 'noise 0.5s infinite'
                  }}></div>
                
                <style>
                  {`
                    @keyframes noise {
                      0%, 100% { background-position: 0 0 }
                      10% { background-position: -5% -10% }
                      20% { background-position: -15% 5% }
                      30% { background-position: 7% -25% }
                      40% { background-position: 20% 25% }
                      50% { background-position: -25% 10% }
                      60% { background-position: 15% 5% }
                      70% { background-position: 0% 15% }
                      80% { background-position: 25% 10% }
                      90% { background-position: -10% 10% }
                    }
                  `}
                </style>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex flex-col transform transition-all duration-300 hover:translate-x-2 group/item">
                    <span className="text-cyan-400 text-sm uppercase tracking-widest mb-2 group-hover/item:text-cyan-300">Category</span>
                    <span className="text-xl font-medium text-white group-hover/item:text-cyan-50">{productDetails.category}</span>
                    <div className="w-0 group-hover/item:w-full h-px bg-cyan-400/50 mt-2 transition-all duration-300"></div>
                  </div>
                  
                  <div className="flex flex-col transform transition-all duration-300 hover:translate-x-2 group/item">
                    <span className="text-cyan-400 text-sm uppercase tracking-widest mb-2 group-hover/item:text-cyan-300">Price</span>
                    <span className="text-xl font-bold text-green-400 group-hover/item:text-green-300">LKR {productDetails.cost || productDetails.price}</span>
                    <div className="w-0 group-hover/item:w-full h-px bg-green-400/50 mt-2 transition-all duration-300"></div>
                  </div>
                  
                  <div className="flex flex-col transform transition-all duration-300 hover:translate-x-2 group/item">
                    <span className="text-cyan-400 text-sm uppercase tracking-widest mb-2 group-hover/item:text-cyan-300">Stock</span>
                    <span className="text-xl font-medium text-white group-hover/item:text-cyan-50">{productDetails.displayedStock}</span>
                    <div className="w-0 group-hover/item:w-full h-px bg-cyan-400/50 mt-2 transition-all duration-300"></div>
                  </div>
                  
                  <div className="flex flex-col transform transition-all duration-300 hover:translate-x-2 group/item">
                    <span className="text-cyan-400 text-sm uppercase tracking-widest mb-2 group-hover/item:text-cyan-300">Availability</span>
                    <span className={`text-xl font-medium ${productDetails.availability === 'In Stock' ? 'text-green-400 group-hover/item:text-green-300' : 'text-red-400 group-hover/item:text-red-300'}`}>
                      {productDetails.availability}
                    </span>
                    <div className={`w-0 group-hover/item:w-full h-px ${productDetails.availability === 'In Stock' ? 'bg-green-400/50' : 'bg-red-400/50'} mt-2 transition-all duration-300`}></div>
                  </div>
                  
                  <div className="flex flex-col transform transition-all duration-300 hover:translate-x-2 group/item">
                    <span className="text-cyan-400 text-sm uppercase tracking-widest mb-2 group-hover/item:text-cyan-300">State</span>
                    <span className="text-xl font-medium text-white group-hover/item:text-cyan-50">{productDetails.state}</span>
                    <div className="w-0 group-hover/item:w-full h-px bg-cyan-400/50 mt-2 transition-all duration-300"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Specs Array - Gaming Terminal Style */}
          {Array.isArray(productDetails.specs) && productDetails.specs.length > 0 && (
            <div className="bg-gray-900/80 backdrop-blur-lg rounded-lg p-8 border border-gray-700 relative group hover:border-cyan-500/30 transition-all duration-300">
              {/* Terminal Bracket Corner elements with increased border width */}
              <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-cyan-400/60 group-hover:border-cyan-400/80 transition-all duration-300"
                style={{borderTopWidth: '3px', borderLeftWidth: '3px'}}></div>
              <div className="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 border-cyan-400/60 group-hover:border-cyan-400/80 transition-all duration-300"
                style={{borderTopWidth: '3px', borderRightWidth: '3px'}}></div>
              <div className="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 border-cyan-400/60 group-hover:border-cyan-400/80 transition-all duration-300"
                style={{borderBottomWidth: '3px', borderLeftWidth: '3px'}}></div>
              <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-cyan-400/60 group-hover:border-cyan-400/80 transition-all duration-300"
                style={{borderBottomWidth: '3px', borderRightWidth: '3px'}}></div>
              
              {/* Cyber HUD Lines */}
              <div className="absolute top-12 left-12 w-16 h-px bg-cyan-400/30"></div>
              <div className="absolute top-12 right-12 w-16 h-px bg-cyan-400/30"></div>
              <div className="absolute bottom-12 left-12 w-16 h-px bg-cyan-400/30"></div>
              <div className="absolute bottom-12 right-12 w-16 h-px bg-cyan-400/30"></div>
              
              <h3 className="text-2xl font-black mb-8 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 flex items-center uppercase tracking-widest">
                <svg className="w-8 h-8 mr-3 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd"></path>
                </svg>
                Tech Specifications
                <div className="ml-4 h-px flex-grow bg-gradient-to-r from-purple-500/50 to-transparent"></div>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {productDetails.specs.map((s, idx) => (
                  <div key={s._id} className="flex items-center p-4 rounded bg-gray-800/80 hover:bg-gray-700/80 transition-all duration-300 transform hover:-translate-y-1 hover:translate-x-1 border-l-2 border-purple-500/80 group/spec relative overflow-hidden"
                    style={{borderLeftWidth: '3px'}}>
                    {/* Hover animation background */}
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 to-cyan-600/10 translate-x-full group-hover/spec:translate-x-0 transition-transform duration-500"></div>
                    
                    <span className="text-cyan-400 font-medium mr-2 group-hover/spec:text-cyan-300 transition-colors relative z-10">{s.key}:</span> 
                    <span className="text-white group-hover/spec:text-gray-100 relative z-10">{s.value}</span>
                    
                    {/* Little decorative chip element */}
                    <div className="absolute top-0 right-0 w-6 h-2 bg-purple-500/50 group-hover/spec:bg-purple-500/80 transition-colors"></div>
                  </div>
                ))}
              </div>              

            </div>
          )} 
        </>
      )}
    </div>
  </div>
)}
    </div>
  );
};

export default BudgetBuildDetail;