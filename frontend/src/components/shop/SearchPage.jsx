import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { HiSearch, HiTag } from 'react-icons/hi';
import axios from 'axios';
import productsData from '../../data/products.json';

const SearchPage = () => {
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [specifications, setSpecifications] = useState({
        productType: '',
        specs: '',
        purpose: ''
    });
    const [aiTags, setAiTags] = useState([]);
    const [filteredProducts, setFilteredProducts] = useState([]);
    const [aiInsights, setAiInsights] = useState({});

    // AI Specification Processing
    const processSpecifications = async (specs) => {
        try {
            const response = await axios.post('/api/ai/process-specifications', {
                specifications: specs
            });
            return response.data.tags;
        } catch (error) {
            console.error('AI Processing Error:', error);
            return [];
        }
    };

    // Handle Specification Form Submit
    const handleSpecificationSubmit = async (e) => {
        e.preventDefault();
        const generatedTags = await processSpecifications(specifications);
        setAiTags(generatedTags);
    };

    // Add AI Tag to Search
    const addAITagToSearch = (tag) => {
        setQuery(prev => `${prev} ${tag}`.trim());
        document.getElementById('searchInput').focus();
    };

    // Enhanced AI-powered Search
    const handleSearch = async (event) => {
        const value = event.target.value.toLowerCase();
        setQuery(value);
        
        try {
            const response = await axios.post('/api/ai/search', {
                query: value,
                tags: aiTags,
                products: productsData
            });
            setFilteredProducts(response.data.suggestions);
        } catch (error) {
            console.error('Search Error:', error);
            const filtered = productsData.filter(product =>
                product.name.toLowerCase().includes(value) ||
                product.category.toLowerCase().includes(value) ||
                aiTags.some(tag => product.tags?.includes(tag))
            );
            setFilteredProducts(filtered);
        }
    };

    return (
        <div className="bg-gray-900 text-white min-h-screen p-6">
            <div className="container mx-auto max-w-4xl">
                <h1 className="text-3xl font-bold text-center mb-6">AI Product Finder</h1>
                
                {/* Specification Form */}
                <div className="bg-gray-800 p-6 rounded-lg mb-8">
                    <h2 className="text-xl font-semibold mb-4 flex items-center">
                        <HiTag className="mr-2" /> Describe Your Needs
                    </h2>
                    <form onSubmit={handleSpecificationSubmit} className="space-y-4">
                        <div>
                            <label className="block mb-2">Product Type</label>
                            <input
                                type="text"
                                placeholder="e.g., Laptop, Smartphone, etc."
                                className="w-full p-2 rounded text-gray-400"
                                value={specifications.productType}
                                onChange={e => setSpecifications(prev => ({
                                    ...prev,
                                    productType: e.target.value
                                }))}
                            />
                        </div>
                        
                        <div>
                            <label className="block mb-2">Specifications</label>
                            <input
                                type="text"
                                placeholder="e.g., 16GB RAM, 1TB SSD, RTX 3080"
                                className="w-full p-2 rounded text-gray-400"
                                value={specifications.specs}
                                onChange={e => setSpecifications(prev => ({
                                    ...prev,
                                    specs: e.target.value
                                }))}
                            />
                        </div>
                        
                        <div>
                            <label className="block mb-2">Primary Usage</label>
                            <select
                                className="w-full p-2 rounded text-gray-400"
                                value={specifications.purpose}
                                onChange={e => setSpecifications(prev => ({
                                    ...prev,
                                    purpose: e.target.value
                                }))}
                            >
                                <option value="">Select Purpose</option>
                                <option value="gaming">Gaming</option>
                                <option value="business">Business</option>
                                <option value="creative">Creative Work</option>
                                <option value="general">General Use</option>
                            </select>
                        </div>
                        
                        <button
                            type="submit"
                            className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg"
                        >
                            Generate AI Tags
                        </button>
                    </form>
                    
                    {/* AI Generated Tags */}
                    {aiTags.length > 0 && (
                        <div className="mt-6">
                            <h3 className="text-lg font-semibold mb-3">AI Suggestions</h3>
                            <div className="flex flex-wrap gap-2">
                                {aiTags.map((tag, index) => (
                                    <button
                                        key={index}
                                        onClick={() => addAITagToSearch(tag)}
                                        className="bg-blue-600 px-3 py-1 rounded-md hover:bg-blue-700 flex items-center"
                                    >
                                        <HiSearch className="mr-1" /> {tag}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Search Interface */}
                <div className="relative mb-8">
                    <input
                        id="searchInput"
                        type="text"
                        placeholder="Search using AI tags or product names..."
                        value={query}
                        onChange={handleSearch}
                        className="w-full p-4 rounded-lg text-white text-lg"
                    />
                    <HiSearch className="absolute right-4 top-4 text-gray-300 text-2xl" />
                </div>

                {/* ... (rest of your existing inventory insights and results sections) ... */}
            </div>
        </div>
    );
};

export default SearchPage;