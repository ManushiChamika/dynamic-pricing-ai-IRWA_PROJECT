import React, { useState, useEffect, useContext } from "react";
import axios from "axios";
import UploadImage from "./UploadImage";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../../../../context/authContext";
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const AddProduct = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [selectedProductType, setSelectedProductType] = useState("");
  const [filtersList, setFiltersList] = useState([]); // For dynamic product type selection
  const [configData, setConfigData] = useState(null);
  const [product, setProduct] = useState({
    price: "",
    availability: "",
    state: "",
    description: "",
    additionalSpecs: [],
  });
  const [newSpec, setNewSpec] = useState({ key: "", value: "" });
  const [image, setImage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});

  // Fetch the list of all filters for dynamic product type selection
  useEffect(() => {
    axios.get("http://localhost:5000/api/filters")
      .then((res) => {
        setFiltersList(res.data);
      })
      .catch((err) =>
        console.error("Error fetching filters list:", err)
      );
  }, []);

  // Fetch configuration for the selected product type
  useEffect(() => {
    if (selectedProductType) {
      axios
        .get(`http://localhost:5000/api/filters/${selectedProductType}`)
        .then((res) => {
          setConfigData(res.data);
        })
        .catch((err) =>
          console.error("Error fetching filter configuration:", err)
        );
    }
  }, [selectedProductType]);

  const handleProductTypeSelect = (type) => {
    setSelectedProductType(type);
    setProduct((prev) => ({
      ...prev,
      category: type,
    }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProduct((prev) => ({
      ...prev,
      [name]: value,
    }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const handleAddSpec = () => {
    if (newSpec.key && newSpec.value) {
      setProduct((prev) => ({
        ...prev,
        additionalSpecs: [...prev.additionalSpecs, newSpec],
      }));
      setNewSpec({ key: "", value: "" });
    }
  };

  const handleDeleteSpec = (index) => {
    setProduct((prev) => ({
      ...prev,
      additionalSpecs: prev.additionalSpecs.filter((_, i) => i !== index),
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!product.price) {
      newErrors.price = "Price is required.";
    } else if (isNaN(product.price) || Number(product.price) <= 0) {
      newErrors.price = "Enter a valid price greater than 0";
    } else if (
      configData &&
      configData.priceRange &&
      (Number(product.price) < configData.priceRange.min ||
        Number(product.price) > configData.priceRange.max)
    ) {
      newErrors.price = `Price must be between ${configData.priceRange.min} and ${configData.priceRange.max}.`;
    }

    if (!product.availability) {
      newErrors.availability = "Availability is required.";
    }

    if (!product.state) {
      newErrors.state = "State is required.";
    }

    if (!product.description) {
      newErrors.description = "Product description is required.";
    }

    if (configData && configData.options) {
      Object.keys(configData.options).forEach((optionKey) => {
        if (!product[optionKey]) {
          newErrors[optionKey] = `${optionKey} is required.`;
        }
      });
    }

    if (!image) {
      newErrors.image = "Product image is required.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);

    // Combine dynamic options into specs
    const specsFromFields =
      configData && configData.options
        ? Object.keys(configData.options).reduce((acc, key) => {
            if (product[key]) {
              acc.push({ key: key, value: product[key] });
            }
            return acc;
          }, [])
        : [];

    const combinedSpecs = [...specsFromFields, ...product.additionalSpecs];

    const productData = {
      price: product.price,
      availability: product.availability,
      state: product.state,
      description: product.description,
      category: product.category,
      image,
      specs: combinedSpecs,
    };

    try {
      const response = await axios.post("http://localhost:5000/api/products", productData);
      if (response.status === 201) {
        toast.success("Product added successfully!");
        setTimeout(() => {
          // Clear all form fields
          setSelectedProductType("");
          setProduct({
            price: "",
            availability: "",
            state: "",
            description: "",
            additionalSpecs: [],
          });
          setNewSpec({ key: "", value: "" });
          setImage("");
          setErrors({});
          setConfigData(null);
        }, 1500); // enough delay for smooth reset
      }
    } catch (error) {
      console.error("❌ Error adding product:", error);
      toast.error("Error adding product.");
    } finally {
      setIsLoading(false);
    }
    
  };

  const inputClass =
    "w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 text-sm text-gray-800 shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition";
  const textAreaClass =
    "w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 text-sm text-gray-800 shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none";

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-100 to-gray-200 py-12 px-6">
      <div className="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow-lg">
        {/* Add New Filter Button */}
        <div className="flex justify-end mb-4">
          <button
            onClick={() => navigate("/dashboard/filters")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
          >
            Add New Filter
          </button>
        </div>
        <h2 className="text-3xl text-center font-bold text-gray-800 mb-6">Add New Product</h2>
        {!selectedProductType ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
            {filtersList.length > 0 ? (
              filtersList.map((filter) => (
                <button
                  key={filter._id}
                  onClick={() => handleProductTypeSelect(filter.category)}
                  className="px-6 py-4 text-lg font-semibold bg-gradient-to-r from-blue-500 to-blue-700 text-white rounded-lg shadow-md hover:from-blue-600 hover:to-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 transition transform hover:scale-105"
                >
                  {filter.category}
                </button>
              ))
            ) : (
              <p>Loading product types...</p>
            )}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <h3 className="text-2xl font-semibold text-gray-700 underline decoration-4 decoration-blue-500">
              {selectedProductType}
            </h3>
            {configData ? (
              <>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Price</label>
                  <input
                    name="price"
                    type="number"
                    placeholder={`Min: ${configData.priceRange.min} - Max: ${configData.priceRange.max}`}
                    value={product.price !== undefined ? product.price : ''}
                    onChange={(e) => {
                      let value = e.target.value;
                      // Remove leading zeros
                      if (value.length > 1 && value.startsWith('0')) {
                        value = value.replace(/^0+/, '');
                        if (value === '') value = '0'; // if only zeros were there
                      }
                      const numericValue = Number(value);
                      if ((numericValue >= 0 && !isNaN(numericValue)) || value === '') {
                        setProduct((prev) => ({
                          ...prev,
                          price: value === '' ? '' : numericValue
                        }));
                        setErrors((prev) => ({ ...prev, price: "" })); // Clear price error on typing
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === '-' || e.key === 'e' || e.key === '+') {
                        e.preventDefault(); // block minus, exponential, plus
                      }
                    }}
                    className={inputClass}
                  />


                  {errors.price && <p className="text-red-500 text-sm">{errors.price}</p>}
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Availability</label>
                  <select
                    name="availability"
                    value={product.availability}
                    onChange={handleChange}
                    className={inputClass}
                  >
                    <option value="">Select Availability</option>
                    {configData.availability.map((avail) => (
                      <option key={avail} value={avail}>
                        {avail}
                      </option>
                    ))}
                  </select>
                  {errors.availability && <p className="text-red-500 text-sm">{errors.availability}</p>}
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">State</label>
                  <select
                    name="state"
                    value={product.state}
                    onChange={handleChange}
                    className={inputClass}
                  >
                    <option value="">Select State</option>
                    {configData.state.map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                  {errors.state && <p className="text-red-500 text-sm">{errors.state}</p>}
                </div>
                {configData.options &&
                  Object.keys(configData.options).map((optionKey) => (
                    <div key={optionKey} className="space-y-2">
                      <label className="block text-sm font-medium text-gray-700">
                        {optionKey.charAt(0).toUpperCase() + optionKey.slice(1)}
                      </label>
                      <select
                        name={optionKey}
                        value={product[optionKey] || ""}
                        onChange={handleChange}
                        className={inputClass}
                      >
                        <option value="">Select {optionKey}</option>
                        {configData.options[optionKey].map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                      {errors[optionKey] && <p className="text-red-500 text-sm">{errors[optionKey]}</p>}
                    </div>
                  ))}
                <div>
                  <h4 className="text-lg font-semibold text-gray-700">Additional Specifications</h4>
                  {product.additionalSpecs.map((spec, index) => (
                    <div key={index} className="flex items-center space-x-4 mt-2">
                      <span className="text-gray-700">
                        {spec.key}: {spec.value}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleDeleteSpec(index)}
                        className="px-2 py-1 bg-red-500 text-white rounded-md text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <div className="flex space-x-2 mt-4">
                    <input
                      type="text"
                      placeholder="Spec name: e.g., Weight"
                      value={newSpec.key}
                      onChange={(e) =>
                        setNewSpec((prev) => ({ ...prev, key: e.target.value }))
                      }
                      className="flex-1 bg-gray-50 border rounded-lg px-4 py-2"
                    />
                    <input
                      type="text"
                      placeholder="Spec description: e.g., 2.5 kg"
                      value={newSpec.value}
                      onChange={(e) =>
                        setNewSpec((prev) => ({ ...prev, value: e.target.value }))
                      }
                      className="flex-1 bg-gray-50 border rounded-lg px-4 py-2"
                    />
                    <button
                      type="button"
                      onClick={handleAddSpec}
                      className="px-4 py-2 bg-green-500 text-white rounded-md"
                    >
                      Add
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Product Name</label>
                  <textarea
                    name="description"
                    placeholder="e.g., MSI MODERN 15 F13MG INTEL CORE I7"
                    value={product.description}
                    onChange={handleChange}
                    className={textAreaClass}
                  ></textarea>
                  {errors.description && <p className="text-red-500 text-sm">{errors.description}</p>}
                </div>
                <UploadImage name="image" setImage={setImage} />
                {errors.image && <p className="text-red-500 text-sm">{errors.image}</p>}
              </>
            ) : (
              <p>Loading configuration...</p>
            )}
            <div className="flex justify-between items-center mt-6">
              <button
                type="submit"
                className="px-6 py-3 bg-green-500 text-white rounded-lg shadow hover:bg-green-600 focus:outline-none focus:ring focus:ring-green-300 transition"
                disabled={isLoading}
              >
                {isLoading ? "Adding..." : "Add Product"}
              </button>
              <button
                type="button"
                onClick={() => setSelectedProductType("")}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 focus:outline-none focus:ring focus:ring-gray-400 transition"
              >
                Back
              </button>
            </div>
          </form>
        )}
      </div>
      {/* Toast Container for notifications */}
      <ToastContainer position="top-right" autoClose={3000} hideProgressBar />
    </div>
  );
};

export default AddProduct;
