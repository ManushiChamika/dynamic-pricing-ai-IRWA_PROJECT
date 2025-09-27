import React, { useState, useEffect } from "react";
import axios from "axios";
import UploadImage from "../addProduct/UploadImage";

const EditProductModal = ({ product, onClose, onProductUpdated }) => {
  const [configData, setConfigData] = useState(null);
  const [errors, setErrors] = useState({});
  const [formData, setFormData] = useState({
    price: product.price,
    availability: product.availability || "",
    state: product.state || "",
    description: product.description || "",
    image: product.image || "",
    // dynamic fields will be added once config is fetched
  });
  const [additionalSpecs, setAdditionalSpecs] = useState([]);
  const [newSpec, setNewSpec] = useState({ key: "", value: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);

  // Fetch configuration for the product's category
  useEffect(() => {
    if (product.category) {
      axios
        .get(`http://localhost:5000/api/filters/${product.category}`)
        .then((res) => {
          setConfigData(res.data);
        })
        .catch((err) =>
          console.error("Error fetching filter configuration:", err)
        );
    }
  }, [product.category]);

  // Initialize dynamic fields and separate additional specs once configData is available
  useEffect(() => {
    if (configData && configData.options) {
      const dynamicKeys = Object.keys(configData.options);
      const dynamicValues = {};
      const additional = [];

      // Divide product specs between dynamic and additional
      product.specs.forEach((spec) => {
        if (dynamicKeys.includes(spec.key)) {
          dynamicValues[spec.key] = spec.value;
        } else {
          additional.push(spec);
        }
      });

      setFormData((prev) => ({ ...prev, ...dynamicValues }));
      setAdditionalSpecs(additional);
    }
  }, [configData, product.specs]);

  // Handle changes for common and dynamic fields
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Add a new additional spec
  const handleAddSpec = () => {
    if (newSpec.key && newSpec.value) {
      setAdditionalSpecs((prev) => [...prev, newSpec]);
      setNewSpec({ key: "", value: "" });
    }
  };

  // Remove an additional spec
  const handleDeleteSpec = (index) => {
    setAdditionalSpecs((prev) => prev.filter((_, i) => i !== index));
  };

  // Validate required fields and price boundaries
  const validateFields = () => {
    const newErrors = {};
    const price = Number(formData.price);
    if (isNaN(price) || price <= 0) {
      newErrors.price = "Price must be greater than 0.";
    } else if (
      configData &&
      configData.priceRange &&
      price > configData.priceRange.max
    ) {
      newErrors.price = `Price cannot exceed ${configData.priceRange.max}.`;
    }
    if (!formData.availability) {
      newErrors.availability = "Please select availability.";
    }
    if (!formData.state) {
      newErrors.state = "Please select a state.";
    }
    if (!formData.description) {
      newErrors.description = "Description is required.";
    }
    // Additional validations for dynamic fields if needed
    if (configData && configData.options) {
      Object.keys(configData.options).forEach((key) => {
        if (!formData[key]) {
          newErrors[key] = `Please select ${key}.`;
        }
      });
    }
    return newErrors;
  };

  // When saving, combine dynamic specs and additional specs
  const handleSave = async () => {
    const fieldErrors = validateFields();
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length > 0) return;

    setIsLoading(true);

    const dynamicSpecs =
      configData && configData.options
        ? Object.keys(configData.options).reduce((acc, key) => {
            if (formData[key]) {
              acc.push({ key, value: formData[key] });
            }
            return acc;
          }, [])
        : [];

    const combinedSpecs = [...dynamicSpecs, ...additionalSpecs];

    const updatedProduct = {
      ...product,
      price: formData.price,
      availability: formData.availability,
      state: formData.state,
      description: formData.description,
      image: formData.image,
      specs: combinedSpecs,
    };

    try {
      const response = await axios.patch(
        `http://localhost:5000/api/products/${product._id}`,
        updatedProduct
      );
      if (response.status === 200) {
        onProductUpdated(response.data);
        // Instead of closing immediately, show the custom popup
        setShowSuccessPopup(true);
      }
    } catch (error) {
      console.error("Error updating product:", error);
      window.alert("Error updating product.");
    } finally {
      setIsLoading(false);
    }
  };

  const inputClass = "w-full p-2 border rounded-md";

  // When the update is successful, display a custom popup overlay.
  if (showSuccessPopup) {
    return (
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(0, 0, 0, 0.9)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
        }}
      >
        <div
          style={{
            background: "white",
            padding: "20px",
            borderRadius: "8px",
            textAlign: "center",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.6)",
          }}
        >
          <p>Product edited successfully!</p>
          <button
            onClick={onClose}
            style={{
              marginTop: "10px",
              padding: "8px 16px",
              backgroundColor: "#007BFF",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  if (!configData) {
    return (
      <div
        style={{
          position: "fixed",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "rgba(0, 0, 0, 0.6)",
          zIndex: 50,
        }}
      >
        <div style={{ background: "white", padding: "20px", borderRadius: "8px" }}>
          <p>Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        zIndex: 50,
        overflow: "auto",
      }}
    >
      <div
        style={{
          background: "white",
          padding: "32px",
          borderRadius: "8px",
          width: "58.33%", // approx. w-7/12
          maxHeight: "100vh",
          overflow: "auto",
        }}
      >
        <h3 style={{ fontSize: "1.5rem", fontWeight: "bold", marginBottom: "16px" }}>
          Edit Product
        </h3>

        {/* Price */}
        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", fontSize: "1.125rem", fontWeight: "500", color: "#4a5568" }}>
            Price:
          </label>
          <input
            name="price"
            type="number"
            placeholder={`Min: ${configData.priceRange.min} - Max: ${configData.priceRange.max}`}
            value={formData.price}
            onChange={handleChange}
            className={inputClass}
          />
          {errors.price && (
            <p style={{ color: "red", fontSize: "0.875rem", marginTop: "4px" }}>{errors.price}</p>
          )}
        </div>

        {/* Availability */}
        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", fontSize: "1.125rem", fontWeight: "500", color: "#4a5568" }}>
            Availability:
          </label>
          <select
            name="availability"
            value={formData.availability}
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
          {errors.availability && (
            <p style={{ color: "red", fontSize: "0.875rem", marginTop: "4px" }}>{errors.availability}</p>
          )}
        </div>

        {/* State */}
        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", fontSize: "1.125rem", fontWeight: "500", color: "#4a5568" }}>
            State:
          </label>
          <select
            name="state"
            value={formData.state}
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
          {errors.state && (
            <p style={{ color: "red", fontSize: "0.875rem", marginTop: "4px" }}>{errors.state}</p>
          )}
        </div>

        {/* Dynamic Fields */}
        {configData.options &&
          Object.keys(configData.options).map((optionKey) => (
            <div key={optionKey} style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "1.125rem", fontWeight: "500", color: "#4a5568" }}>
                {optionKey.charAt(0).toUpperCase() + optionKey.slice(1)}:
              </label>
              <select
                name={optionKey}
                value={formData[optionKey] || ""}
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
              {errors[optionKey] && (
                <p style={{ color: "red", fontSize: "0.875rem", marginTop: "4px" }}>
                  {errors[optionKey]}
                </p>
              )}
            </div>
          ))}

        {/* Description */}
        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", fontSize: "1.125rem", fontWeight: "500", color: "#4a5568" }}>
            Description:
          </label>
          <textarea
            name="description"
            placeholder="Product Description"
            value={formData.description}
            onChange={handleChange}
            className={inputClass}
          ></textarea>
          {errors.description && (
            <p style={{ color: "red", fontSize: "0.875rem", marginTop: "4px" }}>{errors.description}</p>
          )}
        </div>

        {/* Additional Specifications */}
        <div style={{ marginBottom: "16px" }}>
          <h4 style={{ fontSize: "1.125rem", fontWeight: "600", color: "#4a5568" }}>
            Additional Specifications
          </h4>
          {additionalSpecs.map((spec, index) => (
            <div key={index} style={{ display: "flex", alignItems: "center", gap: "16px", marginTop: "8px" }}>
              <span style={{ color: "#4a5568" }}>
                {spec.key}: {spec.value}
              </span>
              <button
                type="button"
                onClick={() => handleDeleteSpec(index)}
                style={{
                  padding: "4px 8px",
                  backgroundColor: "#e53e3e",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  fontSize: "0.875rem",
                  cursor: "pointer",
                }}
              >
                Remove
              </button>
            </div>
          ))}
          <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
            <input
              type="text"
              placeholder="Spec name: e.g., Weight"
              value={newSpec.key}
              onChange={(e) =>
                setNewSpec((prev) => ({ ...prev, key: e.target.value }))
              }
              style={{
                flex: 1,
                backgroundColor: "#f7fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "8px 16px",
              }}
            />
            <input
              type="text"
              placeholder="Spec description: e.g., 2.5 kg"
              value={newSpec.value}
              onChange={(e) =>
                setNewSpec((prev) => ({ ...prev, value: e.target.value }))
              }
              style={{
                flex: 1,
                backgroundColor: "#f7fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "8px 16px",
              }}
            />
            <button
              type="button"
              onClick={handleAddSpec}
              style={{
                padding: "8px 16px",
                backgroundColor: "#48bb78",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Add
            </button>
          </div>
        </div>

        {/* Image Upload */}
        <div style={{ marginBottom: "16px" }}>
          <UploadImage
            name="image"
            setImage={(img) =>
              setFormData((prev) => ({ ...prev, image: img }))
            }
          />
          {formData.image && (
            <img
              src={formData.image}
              alt="Product"
              style={{
                marginTop: "8px",
                height: "128px",
                objectFit: "cover",
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
              }}
            />
          )}
        </div>

        {/* Buttons */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "16px" }}>
          <button
            onClick={onClose}
            style={{
              padding: "8px 16px",
              backgroundColor: "#a0aec0",
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isLoading}
            style={{
              padding: "8px 16px",
              backgroundColor: "#4299e1",
              color: "white",
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
            }}
          >
            {isLoading ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditProductModal;
