import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiSearch, FiEdit2, FiTrash2, FiPlus, FiX, FiChevronLeft, FiChevronRight } from 'react-icons/fi';

function BlogManage() {
    const [blogs, setBlogs] = useState([]);
    const [filteredBlogs, setFilteredBlogs] = useState([]);
    const [error, setError] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [currentBlog, setCurrentBlog] = useState(null);
    const [showAddForm, setShowAddForm] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [blogsPerPage] = useState(5);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [blogToDelete, setBlogToDelete] = useState(null);
    const navigate = useNavigate();

    // Form state
    const [formData, setFormData] = useState({
        title: '',
        content: '',
        published: false,
        image: null
    });

    const [formErrors, setFormErrors] = useState({
        title: '',
        content: '',
        image: ''
    });

    useEffect(() => {
        const fetchBlogs = async () => {
            setIsLoading(true);
            try {
                const response = await axios.get("http://localhost:5000/api/blogs/allBlogs");
                setBlogs(response.data.allBlogs || []);
                setFilteredBlogs(response.data.allBlogs || []);
            } catch (error) {
                setError(error.message || "Failed to fetch blogs");
            } finally {
                setIsLoading(false);
            }
        };
        fetchBlogs();
    }, []);

    // Search functionality
    useEffect(() => {
        if (searchTerm.trim() === '') {
            setFilteredBlogs(blogs);
        } else {
            const filtered = blogs.filter(blog => 
                blog.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                blog.content.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredBlogs(filtered);
        }
        setCurrentPage(1); // Reset to first page when searching
    }, [searchTerm, blogs]);

    // Pagination logic
    const indexOfLastBlog = currentPage * blogsPerPage;
    const indexOfFirstBlog = indexOfLastBlog - blogsPerPage;
    const currentBlogs = filteredBlogs.slice(indexOfFirstBlog, indexOfLastBlog);
    const totalPages = Math.ceil(filteredBlogs.length / blogsPerPage);

    const paginate = (pageNumber) => setCurrentPage(pageNumber);

    const deleteHandler = async (id) => {
        setBlogToDelete(id);
        setShowDeleteConfirm(true);
    };

    const confirmDelete = async () => {
        try {
            await axios.delete(`http://localhost:5000/api/blogs/allBlogs/${blogToDelete}`);
            setBlogs(blogs.filter(blog => blog._id !== blogToDelete));
            setShowDeleteConfirm(false);
        } catch (error) {
            console.error("Error deleting blog:", error);
            setError("Failed to delete blog");
        }
    };

    const editHandler = (blog) => {
        setCurrentBlog(blog);
        setFormData({
            title: blog.title,
            content: blog.content,
            published: blog.published,
            image: null
        });
        setIsEditing(true);
        setShowAddForm(true);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const validateForm = () => {
        let valid = true;
        const newErrors = {
            title: '',
            content: '',
            image: ''
        };

        if (!formData.title.trim()) {
            newErrors.title = 'Title is required';
            valid = false;
        } else if (formData.title.length > 100) {
            newErrors.title = 'Title must be less than 100 characters';
            valid = false;
        }

        if (!formData.content.trim()) {
            newErrors.content = 'Content is required';
            valid = false;
        }

        if (!isEditing && !formData.image) {
            newErrors.image = 'Image is required';
            valid = false;
        }

        setFormErrors(newErrors);
        return valid;
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData({
            ...formData,
            [name]: type === 'checkbox' ? checked : value
        });
        
        // Clear error when user starts typing
        if (formErrors[name]) {
            setFormErrors({
                ...formErrors,
                [name]: ''
            });
        }
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && !file.type.match('image.*')) {
            setFormErrors({
                ...formErrors,
                image: 'Please upload an image file (JPEG, JPG, PNG)'
            });
            return;
        }
        
        setFormData({
            ...formData,
            image: file
        });
        
        if (formErrors.image) {
            setFormErrors({
                ...formErrors,
                image: ''
            });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) return;
        
        const data = new FormData();
        data.append('title', formData.title);
        data.append('content', formData.content);
        data.append('published', formData.published);
        if (formData.image) {
            data.append('image', formData.image);
        }

        try {
            if (isEditing) {
                const response = await axios.put(
                    `http://localhost:5000/api/blogs/allBlogs/${currentBlog._id}`,
                    data,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    }
                );
                setBlogs(blogs.map(blog => blog._id === currentBlog._id ? response.data.blog : blog));
                setIsEditing(false);
            } else {
                const response = await axios.post(
                    "http://localhost:5000/api/blogs/addBlog",
                    data,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    }
                );
                setBlogs([...blogs, response.data.blog]);
            }
            setShowAddForm(false);
            setFormData({
                title: '',
                content: '',
                published: false,
                image: null
            });
        } catch (error) {
            console.error("Error saving blog:", error);
            setError(error.response?.data?.message || "Failed to save blog");
        }
    };

    const cancelEdit = () => {
        setIsEditing(false);
        setShowAddForm(false);
        setFormData({
            title: '',
            content: '',
            published: false,
            image: null
        });
        setFormErrors({
            title: '',
            content: '',
            image: ''
        });
    };

    if (error) return (
        <div className="p-4 text-red-600 bg-red-100 rounded-lg mx-auto max-w-4xl mt-8 animate-fade-in">
            Error: {error}
            <button 
                onClick={() => setError(null)}
                className="ml-4 text-red-800 hover:text-red-900"
            >
                <FiX size={20} />
            </button>
        </div>
    );

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl animate-fade-in">
            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full">
                        <h3 className="text-xl font-semibold mb-4">Confirm Deletion</h3>
                        <p className="mb-6">Are you sure you want to delete this blog? This action cannot be undone.</p>
                        <div className="flex justify-end space-x-3">
                            <button 
                                onClick={() => setShowDeleteConfirm(false)}
                                className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 transition-colors"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={confirmDelete}
                                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-8 gap-4">
                <h1 className="text-3xl font-bold text-gray-800">Blog Management</h1>
                
                <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
                    <div className="relative flex-grow">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <FiSearch className="text-gray-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Search blogs..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    
                    <button 
                        onClick={() => {
                            setIsEditing(false);
                            setShowAddForm(!showAddForm);
                            if (!showAddForm) {
                                window.scrollTo({ top: 0, behavior: 'smooth' });
                            }
                        }} 
                        className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors whitespace-nowrap"
                    >
                        {showAddForm ? (
                            <>
                                <FiX size={18} /> Hide Form
                            </>
                        ) : (
                            <>
                                <FiPlus size={18} /> Add New Blog
                            </>
                        )}
                    </button>
                </div>
            </div>

            {(isEditing || showAddForm) && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-8 animate-slide-down">
                    <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                        {isEditing ? 'Edit Blog' : 'Add New Blog'}
                    </h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Title:</label>
                            <input
                                type="text"
                                name="title"
                                value={formData.title}
                                onChange={handleInputChange}
                                className={`w-full px-3 py-2 border ${formErrors.title ? 'border-red-500' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500`}
                            />
                            {formErrors.title && (
                                <p className="mt-1 text-sm text-red-600">{formErrors.title}</p>
                            )}
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Content:</label>
                            <textarea
                                name="content"
                                value={formData.content}
                                onChange={handleInputChange}
                                rows={8}
                                className={`w-full px-3 py-2 border ${formErrors.content ? 'border-red-500' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500`}
                            />
                            {formErrors.content && (
                                <p className="mt-1 text-sm text-red-600">{formErrors.content}</p>
                            )}
                        </div>
                        <div className="flex items-center">
                            <input
                                type="checkbox"
                                name="published"
                                checked={formData.published}
                                onChange={handleInputChange}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <label className="ml-2 block text-sm text-gray-700">Published</label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Image {!isEditing && '(required)'}:
                            </label>
                            <input
                                type="file"
                                name="image"
                                onChange={handleFileChange}
                                accept="image/jpeg, image/jpg, image/png"
                                className={`block w-full text-sm text-gray-500
                                    file:mr-4 file:py-2 file:px-4
                                    file:rounded-md file:border-0
                                    file:text-sm file:font-semibold
                                    file:bg-blue-50 file:text-blue-700
                                    hover:file:bg-blue-100 ${formErrors.image ? 'border-red-500' : ''}`}
                            />
                            {formErrors.image && (
                                <p className="mt-1 text-sm text-red-600">{formErrors.image}</p>
                            )}
                            {isEditing && !formData.image && (
                                <div className="mt-3">
                                    <p className="text-sm text-gray-500 mb-1">Current Image:</p>
                                    <img 
                                        src={`http://localhost:5000${currentBlog.image}`} 
                                        alt="Current" 
                                        className="max-w-xs rounded-md border border-gray-200"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Upload a new image to replace this one</p>
                                </div>
                            )}
                        </div>
                        <div className="flex space-x-3 pt-2">
                            <button 
                                type="submit" 
                                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                            >
                                {isEditing ? (
                                    <>
                                        <FiEdit2 size={16} /> Update Blog
                                    </>
                                ) : (
                                    <>
                                        <FiPlus size={16} /> Save Blog
                                    </>
                                )}
                            </button>
                            <button 
                                type="button" 
                                onClick={cancelEdit} 
                                className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {isLoading ? (
                <div className="flex justify-center items-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            ) : (
                <div className="bg-white shadow-md rounded-lg overflow-hidden animate-fade-in">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">Content Preview</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Image</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">Created</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {currentBlogs.length > 0 ? (
                                    currentBlogs.map(blog => (
                                        <tr key={blog._id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                <div className="font-semibold">{blog.title}</div>
                                                <div className="text-gray-900 mt-1 md:hidden line-clamp-2">
                                                    {blog.content.substring(0, 60)}...
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate hidden md:table-cell">
                                                {blog.content.substring(0, 100)}...
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <img 
                                                    src={`http://localhost:5000${blog.image}`} 
                                                    alt={blog.title} 
                                                    className="h-10 w-10 rounded-full object-cover"
                                                />
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${blog.published ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                                    {blog.published ? 'Published' : 'Draft'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 hidden sm:table-cell">
                                                {new Date(blog.createdAt).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                <div className="flex space-x-2">
                                                    <button 
                                                        onClick={() => editHandler(blog)}
                                                        className="text-blue-600 hover:text-blue-900 p-1 rounded-full hover:bg-blue-50 transition-colors"
                                                        title="Edit"
                                                    >
                                                        <FiEdit2 size={18} />
                                                    </button>
                                                    <button 
                                                        onClick={() => deleteHandler(blog._id)}
                                                        className="text-red-600 hover:text-red-900 p-1 rounded-full hover:bg-red-50 transition-colors"
                                                        title="Delete"
                                                    >
                                                        <FiTrash2 size={18} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                                            {searchTerm ? 'No blogs match your search.' : 'No blogs found. Create your first blog!'}
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {filteredBlogs.length > blogsPerPage && (
                        <div className="px-6 py-4 flex items-center justify-between border-t border-gray-200">
                            <div className="flex-1 flex justify-between sm:hidden">
                                <button 
                                    onClick={() => paginate(currentPage > 1 ? currentPage - 1 : 1)}
                                    disabled={currentPage === 1}
                                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                                >
                                    Previous
                                </button>
                                <button 
                                    onClick={() => paginate(currentPage < totalPages ? currentPage + 1 : totalPages)}
                                    disabled={currentPage === totalPages}
                                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                                >
                                    Next
                                </button>
                            </div>
                            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                                <div>
                                    <p className="text-sm text-gray-700">
                                        Showing <span className="font-medium">{indexOfFirstBlog + 1}</span> to{' '}
                                        <span className="font-medium">
                                            {indexOfLastBlog > filteredBlogs.length ? filteredBlogs.length : indexOfLastBlog}
                                        </span>{' '}
                                        of <span className="font-medium">{filteredBlogs.length}</span> results
                                    </p>
                                </div>
                                <div>
                                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                                        <button
                                            onClick={() => paginate(currentPage > 1 ? currentPage - 1 : 1)}
                                            disabled={currentPage === 1}
                                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            <span className="sr-only">Previous</span>
                                            <FiChevronLeft size={20} />
                                        </button>
                                        {Array.from({ length: totalPages }, (_, i) => i + 1).map(number => (
                                            <button
                                                key={number}
                                                onClick={() => paginate(number)}
                                                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${currentPage === number ? 'z-10 bg-blue-50 border-blue-500 text-blue-600' : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'}`}
                                            >
                                                {number}
                                            </button>
                                        ))}
                                        <button
                                            onClick={() => paginate(currentPage < totalPages ? currentPage + 1 : totalPages)}
                                            disabled={currentPage === totalPages}
                                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            <span className="sr-only">Next</span>
                                            <FiChevronRight size={20} />
                                        </button>
                                    </nav>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default BlogManage;