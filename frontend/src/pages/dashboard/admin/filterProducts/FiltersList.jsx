import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const FiltersList = () => {
  const [filters, setFilters] = useState([]);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [formData, setFormData] = useState({});
  // This state holds the options as an array of objects for easy editing.
  const [optionsList, setOptionsList] = useState([]);
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);
  const navigate = useNavigate();
  const fixedCategories = ['ram', 'casings', 'processor', 'gpu', 'powersupply', 'storage'];


  

  useEffect(() => {
    fetchFilters();
  }, []);

  const fetchFilters = () => {
    axios.get('http://localhost:5000/api/filters')
      .then(response => setFilters(response.data))
      .catch(err => console.error(err));
  };

  // Open the edit modal and initialize form data and optionsList
  const openEditModal = (filter) => {
    setSelectedFilter(filter);
    setFormData({
      category: filter.category,
      priceRange: filter.priceRange,
      availability: filter.availability,
      state: filter.state,
    });
    // Convert filter.options (an object) to an array for dynamic editing.
    if (filter.options) {
      const list = Object.entries(filter.options).map(([key, values]) => ({
        key,
        values: values.join(', ')
      }));
      setOptionsList(list);
    } else {
      setOptionsList([]);
    }
    setIsEditModalOpen(true);
  };

  const closeEditModal = () => {
    setIsEditModalOpen(false);
    setSelectedFilter(null);
    setOptionsList([]);
  };

  // Open the delete modal for confirmation
  const openDeleteModal = (filter) => {
    if (fixedCategories.includes(filter.category.toLowerCase())) {
      showCustomAlert();
      return;
    }
    setSelectedFilter(filter);
    setIsDeleteModalOpen(true);
  };
  
  const showCustomAlert = () => {
    const alertOverlay = document.createElement("div");
    alertOverlay.className =
      "fixed inset-0 flex items-center justify-center bg-black bg-opacity-70 z-50";
  
    const alertBox = document.createElement("div");
    alertBox.className =
      "relative bg-white p-8 rounded-xl shadow-2xl text-center max-w-sm w-full";
  
    alertBox.innerHTML = `
      <div class="text-red-600 text-5xl mb-4 animate-bounce">⚠️</div>
      <h3 class="text-2xl font-extrabold text-gray-800 mb-3 uppercase tracking-wider">
        Critical Filter
      </h3>
      <p class="text-gray-700 mb-6 leading-relaxed">
        This filter is <strong class="text-red-500">critical</strong> and linked to custom prebuilds.<br/>
        It <strong>cannot be deleted</strong> but can still be edited.
      </p>
      <button id="closeAlertButton" class="mt-4 px-5 py-3 bg-gradient-to-r from-blue-500 to-blue-700 text-white font-bold rounded-full hover:scale-105 transition-transform">
        Okay
      </button>
    `;
  
    alertOverlay.appendChild(alertBox);
    document.body.appendChild(alertOverlay);
  
    // Button event to close alert
    const closeButton = alertBox.querySelector("#closeAlertButton");
    closeButton.addEventListener("click", () => {
      document.body.removeChild(alertOverlay);
    });
  
    // Optional: Prevent background scrolling when alert is open
    document.body.style.overflow = "hidden";
  
    closeButton.addEventListener("click", () => {
      document.body.style.overflow = ""; // Re-enable scrolling
    });
  };
  
  
  

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setSelectedFilter(null);
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`http://localhost:5000/api/filters/${selectedFilter._id}`);
      setFilters(filters.filter(filter => filter._id !== selectedFilter._id));
      closeDeleteModal();
    } catch (err) {
      console.error(err);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();

    // Validate required fields
    if (
      !formData.category ||
      !formData.priceRange ||
      (formData.priceRange.min === undefined || formData.priceRange.min === null || formData.priceRange.min === '') ||
      (formData.priceRange.max === undefined || formData.priceRange.max === null || formData.priceRange.max === '') ||
      !formData.availability ||
      formData.availability.length === 0 ||
      !formData.state ||
      formData.state.length === 0
    ) {
      alert("All fields are required.");
      return;
    }

    // Validate price range
    if (Number(formData.priceRange.min) < 0) {
      alert("Minimum price cannot be less than 0.");
      return;
    }

    // Convert optionsList array into an object where each key maps to an array of values.
    const optionsObject = {};
    optionsList.forEach(option => {
      const key = option.key.trim();
      if (key) {
        optionsObject[key] = option.values.split(',')
          .map(item => item.trim())
          .filter(item => item);
      }
    });
    
    const updatedData = {
      ...formData,
      options: optionsObject
    };

    try {
      const response = await axios.put(`http://localhost:5000/api/filters/${selectedFilter._id}`, updatedData);
      const updatedFilter = response.data;
      setFilters(filters.map(filter => filter._id === updatedFilter._id ? updatedFilter : filter));
      // Show success popup on update
      setShowSuccessPopup(true);
    } catch (err) {
      console.error(err);
    }
  };

  // Handlers for simple text changes in the main form
  const handleChange = (e) => {
    const { name, value } = e.target;
    // For priceRange fields, update nested value accordingly.
    if(name === 'priceMin') {
      setFormData({ 
        ...formData, 
        priceRange: { ...formData.priceRange, min: Number(value) } 
      });
    } else if(name === 'priceMax') {
      setFormData({ 
        ...formData, 
        priceRange: { ...formData.priceRange, max: Number(value) } 
      });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  // Handlers for dynamic options list
  const handleOptionChange = (index, field, value) => {
    const newOptionsList = [...optionsList];
    newOptionsList[index][field] = value;
    setOptionsList(newOptionsList);
  };

  const addOption = () => {
    setOptionsList([...optionsList, { key: '', values: '' }]);
  };

  const removeOption = (index) => {
    const newOptionsList = optionsList.filter((_, i) => i !== index);
    setOptionsList(newOptionsList);
  };

  const closeSuccessPopup = () => {
    setShowSuccessPopup(false);
    closeEditModal();
    // Optionally, reload filters or navigate to a route:
    fetchFilters();
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <h1 className="text-3xl font-bold mb-8 text-center text-blue-200">
        Filter Configurations
      </h1>
      <div className="space-y-6">
        {filters.map(filter => (
          <div key={filter._id} className="bg-gray-800 p-6 rounded shadow-md">
            <h3 className="text-2xl font-semibold mb-2 text-gray-100">
              {filter.category}
            </h3>
            <p className="text-gray-300 mb-1">
              Price Range: {filter.priceRange.min} - {filter.priceRange.max}
            </p>
            <p className="text-gray-300 mb-1">
              Availability: {filter.availability.join(', ')}
            </p>
            <p className="text-gray-300 mb-3">
              State: {filter.state.join(', ')}
            </p>
            {filter.options && (
              <div className="mb-4">
                <h4 className="text-lg text-gray-200 mb-2">Options:</h4>
                <div className="space-y-2">
                  {Object.entries(filter.options).map(([key, values]) => (
                    <div key={key} className="p-2 bg-gray-700 rounded shadow-sm">
                      <div className="text-gray-100 font-bold">{key}</div>
                      <div className="flex flex-wrap mt-1">
                        {values.map((value, i) => (
                          <span
                            key={i}
                            className="mr-2 mb-1 px-2 py-1 bg-blue-600 text-white rounded-full text-sm"
                          >
                            {value}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="flex space-x-4">
              <button 
                onClick={() => openEditModal(filter)}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                Edit
              </button>
              <button 
                onClick={() => openDeleteModal(filter)}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-400"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="absolute inset-0 bg-black opacity-95" onClick={closeEditModal}></div>
          <div className="bg-gray-800 p-6 rounded shadow-md z-10 w-150 overflow-y-auto max-h-full">
            <h2 className="text-xl font-bold text-gray-100 mb-4">Edit Filter</h2>
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-gray-300">Category</label>
                <input
                  type="text"
                  name="category"
                  value={formData.category || ''}
                  onChange={handleChange}
                  placeholder="Enter category"
                  required
                  className="w-full p-2 rounded bg-gray-700 text-gray-100"
                />
              </div>
              <div>
                <label className="block text-gray-300">Price Range</label>
                <div className="flex space-x-2">
                <input
                  type="number"
                  name="priceMin"
                  value={formData.priceRange?.min !== undefined ? formData.priceRange.min : ''}
                  onChange={(e) => {
                    let value = e.target.value;
                    // Remove leading zeros (only if more than 1 digit)
                    if (value.length > 1 && value.startsWith('0')) {
                      value = value.replace(/^0+/, '');
                      if (value === '') value = '0'; // In case user deletes everything
                    }
                    const numericValue = Number(value);
                    if (numericValue >= 0 || value === '') {
                      setFormData({
                        ...formData,
                        priceRange: {
                          ...formData.priceRange,
                          min: value === '' ? '' : numericValue
                        }
                      });
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === '-' || e.key === 'e') {
                      e.preventDefault();
                    }
                  }}
                  min="0"
                  placeholder="Min (0 or greater)"
                  required
                  className="w-1/2 p-2 rounded bg-gray-700 text-gray-100"
                />

                <input
                  type="number"
                  name="priceMax"
                  value={formData.priceRange?.max !== undefined ? formData.priceRange.max : ''}
                  onChange={(e) => {
                    let value = e.target.value;
                    if (value.length > 1 && value.startsWith('0')) {
                      value = value.replace(/^0+/, '');
                      if (value === '') value = '0';
                    }
                    const numericValue = Number(value);
                    if (numericValue >= 0 || value === '') {
                      setFormData({
                        ...formData,
                        priceRange: {
                          ...formData.priceRange,
                          max: value === '' ? '' : numericValue
                        }
                      });
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === '-' || e.key === 'e') {
                      e.preventDefault();
                    }
                  }}
                  min="0"
                  placeholder="Max"
                  required
                  className="w-1/2 p-2 rounded bg-gray-700 text-gray-100"
                />



                </div>
              </div>
              <div>
                <label className="block text-gray-300">Availability (comma separated)</label>
                <input
                  type="text"
                  name="availability"
                  value={formData.availability ? formData.availability.join(', ') : ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    availability: e.target.value.split(',').map(item => item.trim())
                  })}
                  placeholder="e.g., in stock, out of stock"
                  required
                  className="w-full p-2 rounded bg-gray-700 text-gray-100"
                />
              </div>
              <div>
                <label className="block text-gray-300">State (comma separated)</label>
                <input
                  type="text"
                  name="state"
                  value={formData.state ? formData.state.join(', ') : ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    state: e.target.value.split(',').map(item => item.trim())
                  })}
                  placeholder="e.g., CA, NY"
                  required
                  className="w-full p-2 rounded bg-gray-700 text-gray-100"
                />
              </div>
              {/* Dynamic Options Editor */}
              <div>
                <label className="block text-gray-300 mb-2">Options</label>
                {optionsList.map((option, index) => (
                  <div key={index} className="flex items-center space-x-2 mb-2">
                    <input
                      type="text"
                      placeholder="Key"
                      value={option.key}
                      onChange={(e) => handleOptionChange(index, 'key', e.target.value)}
                      className="w-1/3 p-2 rounded bg-gray-700 text-gray-100"
                    />
                    <input
                      type="text"
                      placeholder="Comma separated values"
                      value={option.values}
                      onChange={(e) => handleOptionChange(index, 'values', e.target.value)}
                      className="w-1/2 p-2 rounded bg-gray-700 text-gray-100"
                    />
                    {fixedCategories.includes(selectedFilter?.category.toLowerCase())
                     ? (
                      <button
                        disabled
                        title="This filter cannot be deleted because it is used in custom prebuilds."
                        className="px-4 py-2 bg-gray-500 text-white rounded opacity-50 cursor-not-allowed"
                      >
                        Cannot Delete
                      </button>
                    ) : (
                      <button 
                        onClick={() => openDeleteModal(filter)}
                        className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-400"
                      >
                        Delete
                      </button>
                    )}

                  </div>
                ))}
                <button 
                  type="button" 
                  onClick={addOption}
                  className="px-4 py-2 bg-green-500 text-white rounded"
                >
                  Add Option
                </button>
              </div>
              <div className="flex justify-end space-x-4">
                <button 
                  type="button" 
                  onClick={closeEditModal} 
                  className="px-4 py-2 bg-gray-600 text-white rounded"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 bg-blue-500 text-white rounded"
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Success Popup Modal */}
      {showSuccessPopup && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="absolute inset-0 bg-black opacity-50"></div>
          <div className="bg-white p-6 rounded shadow-lg z-10 text-center">
            <h3 className="text-xl font-bold mb-4">Filter Updated!</h3>
            <p className="mb-6">Your filter has been successfully saved.</p>
            <button
              onClick={closeSuccessPopup}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              OK
            </button>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="absolute inset-0 bg-black opacity-50" onClick={closeDeleteModal}></div>
          <div className="bg-gray-800 p-6 rounded shadow-md z-10 w-96">
            <h2 className="text-xl font-bold text-gray-100 mb-4">Confirm Delete</h2>
            <p className="text-gray-300 mb-4">
              Are you sure you want to delete the filter for <strong>{selectedFilter?.category}</strong>?
            </p>
            <div className="flex justify-end space-x-4">
              <button 
                onClick={closeDeleteModal} 
                className="px-4 py-2 bg-gray-600 text-white rounded"
              >
                Cancel
              </button>
              <button 
                onClick={handleDelete} 
                className="px-4 py-2 bg-red-500 text-white rounded"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default FiltersList;
