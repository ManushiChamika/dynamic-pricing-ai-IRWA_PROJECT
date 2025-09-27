import React, { useState, useEffect } from "react";
import ProductCards from "../ProductCards";
import { FiLoader } from "react-icons/fi";
import { useLocation } from "react-router-dom";

const SearchPage = () => {
  const [products, setProducts] = useState([]);
  const [tags, setTags] = useState({ categories: [] });
  const [searchTerm, setSearchTerm] = useState("");
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [showLoader, setShowLoader] = useState(false);

  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const query = params.get("q");
    if (query) {
      setSearchTerm(query);
    }
  }, [location.search]);

  // Fetch products from the database
  useEffect(() => {
    setLoadingProducts(true);
    fetch("http://localhost:5000/api/products")
      .then((res) => res.json())
      .then((data) => {
        setProducts(data);

        const categories = Array.from(
          new Set(data.map((product) => product.category))
        );

        const specs = data
          .map((product) =>
            product.specs?.map((spec) => `${spec.key}: ${spec.value}`) || []
          )
          .flat();
        const uniqueSpecs = Array.from(new Set(specs));

        setTags({ categories, specs: uniqueSpecs });
      })
      .catch((err) => console.error("Error fetching products:", err))
      .finally(() => {
        setLoadingProducts(false);
      });
  }, []);

  // Delayed loader effect
  useEffect(() => {
    let timer;
    if (loadingProducts) {
      timer = setTimeout(() => {
        setShowLoader(true);
      }, 1500);
    } else {
      setShowLoader(false);
    }
    return () => clearTimeout(timer);
  }, [loadingProducts]);

  const handleTagClick = (tag) => {
    setSearchTerm(tag);
  };

  const filteredProducts = products.filter((product) => {
    const searchWords = searchTerm.toLowerCase().split(/\s+/).filter(Boolean);
    const searchableFields = [
      product.name,
      product.category,
      product.availability,
      product.state,
      product.description,
      ...(product.specs?.map((spec) => `${spec.key} ${spec.value}`) || []),
      ...(product.tags || []),
    ];
    const searchableText = searchableFields
      .filter((field) => typeof field === "string")
      .join(" ")
      .toLowerCase();
    return searchWords.some((word) => searchableText.includes(word));
  });

  return (
    <div className="min-h-screen py-12 bg-gradient-to-r from-gray-900 to-blue-900">
      <div className="container mx-auto px-4">
        <div className="bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          {/* Search Bar */}
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full p-4 mb-6 bg-gray-700 border border-gray-600 rounded-lg shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          />

          {/* Filter Tags */}
          <div className="mb-6">
            <h3 className="font-semibold text-xl text-blue-400 mb-3">
              Common Category Tags:
            </h3>
            <div className="flex flex-wrap gap-4">
              {tags.categories.map((category, idx) => (
                <span
                  key={idx}
                  onClick={() => handleTagClick(category)}
                  className="bg-blue-600 text-white px-5 py-2 rounded-full cursor-pointer hover:bg-blue-700 transition-transform transform hover:scale-105"
                >
                  {category}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Display Loading Spinner or Filtered Products */}
        <div>
          {loadingProducts && showLoader ? (
            <div className="flex justify-center items-center py-4">
              <FiLoader className="text-white animate-spin text-3xl" />
            </div>
          ) : filteredProducts.length ? (
            <ProductCards products={filteredProducts} />
          ) : (
            <div className="flex flex-col justify-center items-center py-8 bg-gray-800 text-white rounded-lg shadow-lg">
              <h2 className="text-3xl font-bold mb-4">No Products Found</h2>
              <p className="text-lg">
                Oops! Looks like there are no products matching your search. Try exploring different categories or updating your search term.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPage;