import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import { FaMicrochip, FaLaptop, FaGamepad } from 'react-icons/fa';

function UserBlog() {
    const [blogs, setBlogs] = useState([]);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [currentSlide, setCurrentSlide] = useState(0);

    useEffect(() => {
        const fetchBlogs = async () => {
            setIsLoading(true);
            try {
                const response = await axios.get("http://localhost:5000/api/blogs/allBlogs");
                const publishedBlogs = response.data.allBlogs.filter(blog => blog.published);
                setBlogs(publishedBlogs || []);
            } catch (error) {
                setError(error.message || "Failed to fetch blogs");
            } finally {
                setIsLoading(false);
            }
        };
        fetchBlogs();
    }, []);

    const nextSlide = () => {
        setCurrentSlide((prev) => (prev === blogs.length - 1 ? 0 : prev + 1));
    };

    const prevSlide = () => {
        setCurrentSlide((prev) => (prev === 0 ? blogs.length - 1 : prev - 1));
    };

    useEffect(() => {
        if (blogs.length > 1) {
            const timer = setInterval(() => {
                nextSlide();
            }, 5000);
            return () => clearInterval(timer);
        }
    }, [blogs.length, currentSlide]);

    if (error) return (
        <div className="p-4 text-red-600 bg-red-100 rounded-lg mx-auto max-w-4xl mt-8">
            Error: {error}
        </div>
    );

    if (isLoading) return (
        <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
    );

    if (blogs.length === 0) return (
        <div className="text-center py-8">
            <p className="text-gray-500">No published blogs available at the moment.</p>
        </div>
    );

    const getCategoryIcon = (title) => {
        const lowerTitle = title.toLowerCase();
        if (lowerTitle.includes('gaming') || lowerTitle.includes('game')) return <FaGamepad className="text-purple-400 mr-2" />;
        if (lowerTitle.includes('laptop') || lowerTitle.includes('notebook')) return <FaLaptop className="text-blue-400 mr-2" />;
        return <FaMicrochip className="text-green-400 mr-2" />;
    };

    return (
        <section className="pb-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-gray-900 to-gray-800 relative overflow-hidden shadow-xl rounded-lg">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(45,55,72,0.6)_0%,rgba(0,0,0,0.9)_75%)] opacity-70 z-0"></div>

            <div className="max-w-5xl mx-auto relative z-10">
                <div className="text-center mb-10">
                    <span className="inline-block px-4 py-1 text-sm font-semibold text-cyan-300 bg-gray-800 rounded-full mb-4 shadow-md">
                        Explore Our Insights
                    </span>
                    <h2 className="text-3xl font-bold text-white sm:text-4xl bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-lime-400">
                        The Tech Scoop
                    </h2>
                    <p className="mt-3 max-w-2xl mx-auto text-lg text-gray-400">
                        Stay informed with the latest trends, reviews, and guides in the world of computers and technology.
                    </p>
                </div>

                <div className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl blur-lg opacity-0 group-hover:opacity-80 transition duration-500 animate-pulse"></div>

                    <div className="relative overflow-hidden rounded-xl bg-gray-800 bg-opacity-60 backdrop-blur-md border border-gray-700 shadow-lg h-[450px]">
                        <div
                            className="flex transition-transform duration-500 ease-out h-full"
                            style={{ transform: `translateX(-${currentSlide * 100}%)` }}
                        >
                            {blogs.map((blog, index) => (
                                <div key={blog._id} className="w-full flex-shrink-0">
                                    <div className="p-2 h-full">
                                        <div className="flex flex-col md:flex-row h-full rounded-xl overflow-hidden">
                                            <div className="md:w-2/5 relative h-64 md:h-full">
                                                <img
                                                    className="w-full h-full object-cover transform group-hover:scale-105 transition duration-700"
                                                    src={`http://localhost:5000${blog.image}`}
                                                    alt={blog.title}
                                                />
                                                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4 flex items-center justify-start">
                                                    {getCategoryIcon(blog.title)}
                                                    <span className="text-sm font-medium text-gray-200">
                                                        {blog.title.includes('Gaming') ? 'Gaming' :
                                                            blog.title.includes('Laptop') ? 'Laptops' : 'Hardware'}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="md:w-3/5 p-6 flex flex-col justify-center bg-gray-900 bg-opacity-70">
                                                <div className="flex items-center mb-3">
                                                    <span className="text-xs font-semibold px-3 py-1 bg-blue-800 text-blue-300 rounded-full shadow-sm">
                                                        {new Date(blog.createdAt).toLocaleDateString('en-US', {
                                                            month: 'short',
                                                            day: 'numeric',
                                                            year: 'numeric'
                                                        })}
                                                    </span>
                                                </div>
                                                <h3 className="text-xl font-bold text-white mb-2 hover:text-teal-300 transition duration-300">
                                                    {blog.title}
                                                </h3>
                                                <p className="text-gray-400 line-clamp-5 mb-0">
                                                    {blog.content}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <button
                        onClick={prevSlide}
                        className="absolute left-4 top-1/2 -translate-y-1/2 bg-gray-800 bg-opacity-70 p-3 rounded-full shadow-lg text-white hover:text-blue-300 focus:outline-none z-20 transition-all duration-300 hover:bg-gray-700"
                        aria-label="Previous slide"
                    >
                        <FiChevronLeft className="h-6 w-6" />
                    </button>
                    <button
                        onClick={nextSlide}
                        className="absolute right-4 top-1/2 -translate-y-1/2 bg-gray-800 bg-opacity-70 p-3 rounded-full shadow-lg text-white hover:text-blue-300 focus:outline-none z-20 transition-all duration-300 hover:bg-gray-700"
                        aria-label="Next slide"
                    >
                        <FiChevronRight className="h-6 w-6" />
                    </button>

                    <div className="flex justify-center mt-6 space-x-3">
                        {blogs.map((_, index) => (
                            <button
                                key={index}
                                onClick={() => setCurrentSlide(index)}
                                className={`h-3 w-3 rounded-full transition-all duration-300 ${currentSlide === index ? 'bg-cyan-400 w-5 shadow-md' : 'bg-gray-600'}`}
                                aria-label={`Go to slide ${index + 1}`}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}

export default UserBlog;