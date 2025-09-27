import React, { useEffect, useState } from "react";
import axios from "axios";

const EditCustomPreBuild = ({
  build,
  onClose,
  refreshBuilds,
  processorOptions,
  gpuOptions,
  ramOptions,
  storageOptions,
  powerSupplyOptions,
  casingsOptions,
}) => {
  // Use the passed build as initial state (all component fields are stored as product IDs)
  const [preBuild, setPreBuild] = useState({ ...build });
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: "", type: "" });

  // Handler for field changes – works for both text inputs and selects
  const handleChange = (e) => {
    const { name, value } = e.target;
    setPreBuild((prev) => ({ ...prev, [name]: value }));
  };

  // Get product price from options based on id
  const getProductPrice = (id, options) => {
    const prod = options.find((p) => p._id === id);
    return prod ? Number(prod.price) : 0;
  };

  // Recalculate the build price from the selected components
  const recalcPrice = () => {
    const total =
      getProductPrice(preBuild.processor, processorOptions) +
      getProductPrice(preBuild.gpu, gpuOptions) +
      getProductPrice(preBuild.ram, ramOptions) +
      getProductPrice(preBuild.storage, storageOptions) +
      getProductPrice(preBuild.powerSupply, powerSupplyOptions) +
      getProductPrice(preBuild.casings, casingsOptions);
    setPreBuild((prev) => ({ ...prev, price: total }));
  };

  useEffect(() => {
    recalcPrice();
    // We intentionally run this when any of the component selections change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    preBuild.processor,
    preBuild.gpu,
    preBuild.ram,
    preBuild.storage,
    preBuild.powerSupply,
    preBuild.casings,
  ]);

  // Compatibility options handlers
  const handleCompatibilityChange = (category, index, productId) => {
    setPreBuild((prev) => {
      const newCompat = { ...prev.compatibility };
      newCompat[category][index] = productId;
      return { ...prev, compatibility: newCompat };
    });
  };

  const addCompatibilityOption = (category) => {
    setPreBuild((prev) => {
      const newCompat = { ...prev.compatibility };
      newCompat[category] = [...(newCompat[category] || []), ""];
      return { ...prev, compatibility: newCompat };
    });
  };

  const removeCompatibilityOption = (category, index) => {
    setPreBuild((prev) => {
      const newCompat = { ...prev.compatibility };
      newCompat[category] = newCompat[category].filter((_, i) => i !== index);
      return { ...prev, compatibility: newCompat };
    });
  };

  // Notification helper
  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: "", type: "" }), 3000);
  };

  // Submit handler to update the pre-build
  const handleSubmit = async (e) => {
    e.preventDefault();
    // Validate required fields
    if (
      !preBuild.image ||
      !preBuild.category ||
      !preBuild.price ||
      !preBuild.processor ||
      !preBuild.gpu ||
      !preBuild.ram ||
      !preBuild.storage ||
      !preBuild.powerSupply ||
      !preBuild.casings ||
      !preBuild.description
    ) {
      showNotification("All fields are required!", "error");
      return;
    }
    setLoading(true);
    try {
      await axios.put(`http://localhost:5000/api/prebuilds/${preBuild._id}`, preBuild, {
        headers: { "Content-Type": "application/json" },
      });
      showNotification("Pre-build updated successfully!", "success");
      refreshBuilds();
      onClose();
    } catch (error) {
      console.error("Error updating pre-build:", error);
      showNotification("Error updating pre-build. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  };

  // Helper: Given a product id and options, return a description string
  const getProductDescription = (id, options) => {
    const prod = options.find((p) => p._id === id);
    return prod ? `${prod.description} (LKR ${prod.price})` : id;
  };

  return (
    // Modal backdrop
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
      {/* Modal container */}
      <div className="bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 w-11/12 max-w-6xl p-8 overflow-auto max-h-full">
        <div className="flex justify-between items-center mb-8 border-b border-gray-700 pb-4">
          <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
            Edit Custom PC Build
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-xl">&times;</button>
        </div>
        {notification.show && (
          <div className={`mb-6 p-4 rounded-xl flex items-center border ${
            notification.type === "success"
              ? "bg-green-900/20 border-green-500 text-green-400"
              : "bg-red-900/20 border-red-500 text-red-400"
          }`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
              notification.type === "success" ? "bg-green-500/20" : "bg-red-500/20"
            }`}>
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

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Image and Category */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">Image URL</label>
              <input
                type="text"
                name="image"
                value={preBuild.image}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
                placeholder="https://example.com/image.jpg"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">Category</label>
              <select
                name="category"
                value={preBuild.category}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              >
                <option value="Gaming">Gaming</option>
                <option value="Budget">Budget</option>
              </select>
            </div>
          </div>

          {/* Component Dropdowns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Processor */}
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">Processor</label>
              <select
                name="processor"
                value={preBuild.processor}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              >
                <option value="">Select Processor</option>
                {processorOptions.map((prod) => (
                  <option key={prod._id} value={prod._id}>
                    {prod.description} (LKR {prod.price})
                  </option>
                ))}
              </select>
            </div>
            {/* GPU */}
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">GPU</label>
              <select
                name="gpu"
                value={preBuild.gpu}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              >
                <option value="">Select GPU</option>
                {gpuOptions.map((prod) => (
                  <option key={prod._id} value={prod._id}>
                    {prod.description} (LKR {prod.price})
                  </option>
                ))}
              </select>
            </div>
            {/* RAM */}
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">RAM</label>
              <select
                name="ram"
                value={preBuild.ram}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              >
                <option value="">Select RAM</option>
                {ramOptions.map((prod) => (
                  <option key={prod._id} value={prod._id}>
                    {prod.description} (LKR {prod.price})
                  </option>
                ))}
              </select>
            </div>
            {/* Storage */}
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">Storage</label>
              <select
                name="storage"
                value={preBuild.storage}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              >
                <option value="">Select Storage</option>
                {storageOptions.map((prod) => (
                  <option key={prod._id} value={prod._id}>
                    {prod.description} (LKR {prod.price})
                  </option>
                ))}
              </select>
            </div>
            {/* Power Supply */}
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">Power Supply</label>
              <select
                name="powerSupply"
                value={preBuild.powerSupply}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              >
                <option value="">Select Power Supply</option>
                {powerSupplyOptions.map((prod) => (
                  <option key={prod._id} value={prod._id}>
                    {prod.description} (LKR {prod.price})
                  </option>
                ))}
              </select>
            </div>
            {/* Casings */}
            <div className="space-y-2">
              <label className="block text-sm text-gray-300">Casings</label>
              <select
                name="casings"
                value={preBuild.casings}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              >
                <option value="">Select Casings</option>
                {casingsOptions.map((prod) => (
                  <option key={prod._id} value={prod._id}>
                    {prod.description} (LKR {prod.price})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label className="block text-sm text-gray-300">Description</label>
            <textarea
              name="description"
              value={preBuild.description}
              onChange={handleChange}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
              placeholder="Enter build description"
            ></textarea>
          </div>

          {/* Compatibility Options */}
          <div className="space-y-4">
            <h4 className="text-lg text-blue-400">Compatibility Options</h4>
            {["processor", "gpu", "ram", "storage", "powerSupply", "casings"].map((category) => (
              <div key={category} className="mb-2">
                <p className="text-sm text-gray-300 capitalize">{category}</p>
                {preBuild.compatibility[category] && preBuild.compatibility[category].length > 0 ? (
                  preBuild.compatibility[category].map((compId, idx) => (
                    <div key={idx} className="flex items-center space-x-2 mb-1">
                      <select
                        value={compId}
                        onChange={(e) => handleCompatibilityChange(category, idx, e.target.value)}
                        className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:ring-blue-500 focus:border-blue-500 text-gray-200"
                      >
                        <option value="">Select {category}</option>
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
                            <option key={prod._id} value={prod._id}>
                              {prod.description} (LKR {prod.price})
                            </option>
                          ));
                        })()}
                      </select>
                      <button type="button" onClick={() => removeCompatibilityOption(category, idx)} className="px-2 py-1 bg-red-500 text-white rounded">
                        Remove
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-400">None</p>
                )}
                <button type="button" onClick={() => addCompatibilityOption(category)} className="text-blue-400 hover:text-blue-600 text-sm">
                  + Add {category} compatibility option
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-center mt-6">
            <button
              type="submit"
              disabled={loading}
              className="px-8 py-3 rounded-xl bg-blue-500 hover:bg-blue-700 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            >
              {loading ? "Updating..." : "Update Build"}
            </button>
          </div>
        </form>

        {/* Current Specifications Display */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 shadow-lg mt-8">
          <h3 className="text-lg font-medium text-blue-400 mb-4">Current Specifications</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Image</span>
              <span className="text-sm text-gray-200">{preBuild.image}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Category</span>
              <span className="text-sm text-gray-200">{preBuild.category}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Price</span>
              <span className="text-sm text-gray-200">LKR {preBuild.price}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Processor</span>
              <span className="text-sm text-gray-200">{getProductDescription(preBuild.processor, processorOptions)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">GPU</span>
              <span className="text-sm text-gray-200">{getProductDescription(preBuild.gpu, gpuOptions)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">RAM</span>
              <span className="text-sm text-gray-200">{getProductDescription(preBuild.ram, ramOptions)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Storage</span>
              <span className="text-sm text-gray-200">{getProductDescription(preBuild.storage, storageOptions)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Power Supply</span>
              <span className="text-sm text-gray-200">{getProductDescription(preBuild.powerSupply, powerSupplyOptions)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Casings</span>
              <span className="text-sm text-gray-200">{getProductDescription(preBuild.casings, casingsOptions)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-400">Description</span>
              <span className="text-sm text-gray-200">{preBuild.description}</span>
            </div>
            <div>
              <span className="text-sm text-gray-400">Compatibility:</span>
              {preBuild.compatibility ? (
                Object.entries(preBuild.compatibility).map(([cat, arr]) => (
                  <div key={cat} className="text-sm text-gray-200">
                    <strong>{cat}: </strong>
                    {arr.length > 0
                      ? arr
                          .map((prodId) => {
                            let options = [];
                            switch (cat) {
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
                            return getProductDescription(prodId, options);
                          })
                          .join(", ")
                      : "None"}
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-200">None</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditCustomPreBuild;