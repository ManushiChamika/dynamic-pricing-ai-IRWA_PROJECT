import React, { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import qs from "qs";
import ProductList from "./ProductList";

const ProductCategory = () => {
  const { category } = useParams();
  const navigate = useNavigate();

  // Smooth full-page loader
  const Loader = ({ visible, category }) => (
    <div
      className={`fixed inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-700 bg-opacity-90 transition-opacity duration-500 ease-in-out z-50 ${
        visible ? "opacity-100" : "opacity-0 pointer-events-none"
      }`}
    >
      <div className="relative w-20 h-20 mb-6">
        {/* Glowing outer pulse */}
        <div className="absolute inset-0 border-4 border-cyan-400/30 rounded-full animate-ping opacity-80" />
        {/* Rotating spinner */}
        <div className="absolute inset-0 border-4 border-transparent border-t-cyan-400 border-b-cyan-600 rounded-full animate-spin" />
        {/* Soft inner glow */}
        <div className="absolute inset-2 bg-cyan-500 rounded-full blur-xl opacity-30" />
      </div>
  
      <p className="text-cyan-300 text-xl font-extrabold tracking-wide animate-pulse">
        {category ? `Loading ${category.replace(/-/g, " ")}...` : "Loading..."}
      </p>

    </div>
  );


  // State management
  const [categoryFilters, setCategoryFilters] = useState({});
  const [loadingFilters, setLoadingFilters] = useState(true);
  const [filtersError, setFiltersError] = useState(null);
  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [productsError, setProductsError] = useState(null);
  const [displayedProducts, setDisplayedProducts] = useState([]);
  const [showLoader, setShowLoader] = useState(false);

  const limit = 12;
  const [page, setPage] = useState(1);
  const [selectedFilters, setSelectedFilters] = useState({});

  // 🧠 Compute the initial price range
  const initialPriceRange = useMemo(() => {
    if (categoryFilters.priceRange) {
      return [categoryFilters.priceRange.min, categoryFilters.priceRange.max];
    }
    return [0, 1000];
  }, [categoryFilters.priceRange]);

  const [priceRange, setPriceRange] = useState([0, 1000]);

  // Keep priceRange updated with initialPriceRange
  useEffect(() => {
    setPriceRange(initialPriceRange);
  }, [initialPriceRange]);

  // Unified loading state with smooth transition
  useEffect(() => {
    const isLoading = loadingFilters || loadingProducts;
    setShowLoader(isLoading);
  }, [loadingFilters, loadingProducts]);

  // Fetch filter configuration
  useEffect(() => {
    const fetchCategoryFilters = async () => {
      try {
        const response = await axios.get(`http://localhost:5000/api/filters/${category}`);
        setCategoryFilters(response.data);
      } catch (err) {
        setFiltersError("Failed to load filter options.");
      } finally {
        setLoadingFilters(false);
      }
    };
    fetchCategoryFilters();
  }, [category]);

  // Fetch products
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const params = {
          category,
          page,
          limit,
          minPrice: priceRange[0],
          maxPrice: priceRange[1],
          ...selectedFilters
        };

        const response = await axios.get(`http://localhost:5000/api/products`, {
          params,
          paramsSerializer: params => qs.stringify(params, { arrayFormat: "repeat" })
        });

        setProducts(response.data);

        setTimeout(() => {
          setDisplayedProducts(response.data);
        }, 500); // small delay for transition

      } catch (err) {
        setProductsError("Failed to fetch products.");
      } finally {
        setTimeout(() => setLoadingProducts(false), 500); // smooth loading
      }
    };

    if (!loadingFilters) {
      fetchProducts();
    }
  }, [category, page, priceRange, selectedFilters, loadingFilters]);

  // Scroll to top when filters change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [selectedFilters, priceRange]);

  // Handlers
  const handleRadioClick = (filterKey, option) => {
    setSelectedFilters((prev) => ({
      ...prev,
      [filterKey]: prev[filterKey] === option ? undefined : option
    }));
  };

  const clearFilters = () => {
    setSelectedFilters({});
    setPriceRange(initialPriceRange);
    setPage(1);
  };

  return (
    <div className="bg-gray-900 pb-6 min-h-screen">
      <Loader visible={showLoader} />
      <section className="container mx-auto py-8 px-4">
        <div className="mb-4">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-gray-500 text-white font-semibold rounded hover:bg-blue-600 transition cursor-pointer"
          >
            &larr; Back
          </button>
        </div>

        <h2 className="text-4xl font-bold text-blue-500 capitalize mb-6">
          {category}
        </h2>

        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar */}
          <aside className="md:w-1/4 bg-gray-800 p-4 rounded-lg">
            {loadingFilters && <p className="text-white">Loading filter options...</p>}
            {filtersError && <p className="text-red-500">{filtersError}</p>}

            {!loadingFilters && !filtersError && categoryFilters.priceRange && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-white mb-2">Price Range</h4>
                <div className="flex items-center space-x-2">
                  <span className="text-white">{priceRange[0]} LKR</span>
                  <input
                    type="range"
                    min={categoryFilters.priceRange.min}
                    max={categoryFilters.priceRange.max}
                    value={priceRange[1]}
                    onChange={(e) => setPriceRange([priceRange[0], Number(e.target.value)])}
                    className="w-full h-2 bg-gray-600 rounded-lg cursor-pointer accent-blue-500"
                  />
                  <span className="text-white">Up to {priceRange[1]} LKR</span>
                </div>
              </div>
            )}

            <div className="mt-6">
              <button
                onClick={clearFilters}
                className="w-full px-4 py-2 bg-gray-500 text-white font-semibold rounded hover:bg-blue-600 transition cursor-pointer"
              >
                Clear All Filters
              </button>
            </div>

            {/* Other filters */}
            <div className="space-y-4 mt-6">
              {!loadingFilters &&
                !filtersError &&
                Object.keys(categoryFilters)
                  .filter(key => !["priceRange", "_id", "category", "createdAt", "updatedAt", "__v", "options"].includes(key))
                  .map((filterKey) => (
                    <div key={filterKey} className="bg-gray-700 p-3 rounded-lg">
                      <h4 className="text-lg font-semibold text-white mb-2">
                        {filterKey.charAt(0).toUpperCase() + filterKey.slice(1)}
                      </h4>
                      <div className="space-y-2">
                        {Array.isArray(categoryFilters[filterKey]) && categoryFilters[filterKey].map(option => (
                          <label key={option} className="flex items-center gap-2 text-white cursor-pointer">
                            <input
                              type="radio"
                              name={filterKey}
                              value={option}
                              checked={selectedFilters[filterKey] === option}
                              onClick={() => handleRadioClick(filterKey, option)}
                              className="cursor-pointer accent-blue-500"
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))
              }
              {/* options inside nested "options" */}
              {!loadingFilters &&
                !filtersError &&
                categoryFilters.options &&
                Object.keys(categoryFilters.options).map((filterKey) => (
                  <div key={filterKey} className="bg-gray-700 p-3 rounded-lg">
                    <h4 className="text-lg font-semibold text-white mb-2">
                      {filterKey.charAt(0).toUpperCase() + filterKey.slice(1)}
                    </h4>
                    <div className="space-y-2">
                      {categoryFilters.options[filterKey].map(option => (
                        <label key={option} className="flex items-center gap-2 text-white cursor-pointer">
                          <input
                            type="radio"
                            name={filterKey}
                            value={option}
                            checked={selectedFilters[filterKey] === option}
                            onClick={() => handleRadioClick(filterKey, option)}
                            className="cursor-pointer accent-blue-500"
                          />
                          {option}
                        </label>
                      ))}
                    </div>
                  </div>
                ))
              }
            </div>
          </aside>

          {/* Product List */}
          <div className="md:w-3/4 relative">
  {productsError && (
    <p className="text-red-500">{productsError}</p>
  )}

  {!showLoader && displayedProducts.length === 0 && (
    <div className="flex flex-col items-center justify-center text-center py-16 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-700 rounded-lg shadow-lg">
      <div className="text-6xl mb-4 text-yellow-400 animate-bounce">✨</div>
      <h3 className="text-3xl font-extrabold text-white mb-3">Let's Discover Something You Adore!</h3>
      <p className="text-gray-300 mb-6 text-lg">
        Oops, no items here just yet. Check out other categories or tweak your filters to uncover delightful products!
      </p>
      <button
        onClick={() => navigate(-1)}
        className="px-8 py-3 bg-gradient-to-r from-blue-500 to-green-500 text-white font-bold rounded-full hover:shadow-2xl hover:from-green-500 hover:to-blue-500 transition transform hover:-translate-y-1 active:translate-y-0"
      >
        Explore More
      </button>
    </div>
  )}

  <div className={`transition-opacity duration-500 ${showLoader ? 'opacity-0' : 'opacity-100'}`}>
    {displayedProducts.length > 0 && (
      <>
        <ProductList products={displayedProducts} />

        {/* Pagination */}
        <div className="flex justify-center mt-6">
          <button
            className="px-4 py-2 mx-2 bg-gray-700 text-white rounded"
            disabled={page === 1}
            onClick={() => setPage((prev) => prev - 1)}
          >
            Previous
          </button>
          <span className="text-white px-4 py-2">Page {page}</span>
          <button
            className="px-4 py-2 mx-2 bg-gray-700 text-white rounded"
            disabled={products.length < limit}
            onClick={() => setPage((prev) => prev + 1)}
          >
            Next
          </button>
        </div>
      </>
    )}
  </div>
</div>
        </div>
      </section>
    </div>
  );
};

export default ProductCategory;
