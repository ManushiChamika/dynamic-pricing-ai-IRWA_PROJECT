import React, { useState, useEffect, useContext } from "react";
import axios from "axios";
import { AuthContext } from "../../context/authContext";
import { toast } from "react-toastify";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination, Autoplay, EffectCoverflow } from "swiper/modules";

// Import Swiper styles
import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";
import "swiper/css/effect-coverflow";

function ReviewForm() {
    const { user } = useContext(AuthContext);
    const [formData, setFormData] = useState({
        fullName: user?.name || '',
        email: user?.email || '',
        rating: 0,
        comment: '',
        reviewTitle: ''
    });
    const { fullName, email, rating, comment, reviewTitle } = formData;
    const [reviews, setReviews] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        fetchApprovedReviews();
        if (user) {
            setFormData(prev => ({
                ...prev,
                fullName: user.name || '',
                email: user.email || ''
            }));
        }
    }, [user]);

    const fetchApprovedReviews = async () => {
        try {
            const response = await axios.get("http://localhost:5000/api/reviews/approved");
            setReviews(response.data);
        } catch (error) {
            console.error("Error fetching approved reviews:", error);
            toast.error("Failed to load reviews. Please try again later.");
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        
        if (!formData.comment.trim()) {
            toast.error('Comment is required.');
            setIsSubmitting(false);
            return;
        }

        if (!formData.reviewTitle.trim()) {
            toast.error('Review title is required.');
            setIsSubmitting(false);
            return;
        }

        if (formData.rating === 0) {
            toast.error('Please select a rating.');
            setIsSubmitting(false);
            return;
        }

        const token = localStorage.getItem("token");
        if (!user || !token) {
            toast.error("You must be logged in to submit a review.");
            setIsSubmitting(false);
            return;
        }

        try {
            const response = await axios.post(
                "http://localhost:5000/api/reviews/submit",
                formData,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 10000
                }
            );

            toast.success(response.data.message);
            setFormData(prev => ({
                ...prev,
                rating: 0,
                comment: '',
                reviewTitle: ''
            }));
            fetchApprovedReviews();
        } catch (error) {
            console.error("Review submission error:", error);
            const errorMessage = error.response?.data?.message || 
                               error.message || 
                               "Failed to submit review";
            toast.error(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleRatingClick = (value) => {
        setFormData(prev => ({ ...prev, rating: value }));
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-900 via-gray-900 to-black text-white p-4 md:p-8 flex flex-col items-center">
            <div className="max-w-6xl w-full">
                {/* Reviews Slider Section */}
                <section className="mb-16">
                    <h2 className="text-4xl md:text-5xl font-extrabold text-center mb-4 text-blue-400">
                        Customer <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Reviews</span>
                    </h2>
                    <p className="text-lg text-center text-gray-300 mb-8 max-w-2xl mx-auto">
                        Hear what our community says about their experience with us
                    </p>

                    {reviews.length === 0 ? (
                        <div className="bg-gray-800/50 rounded-xl p-8 text-center border border-gray-700">
                            <p className="text-gray-400">No reviews yet. Be the first to share your experience!</p>
                        </div>
                    ) : (
                        <div className="relative px-4">
                            <Swiper
                                modules={[Navigation, Pagination, Autoplay, EffectCoverflow]}
                                effect={'coverflow'}
                                grabCursor={true}
                                centeredSlides={true}
                                slidesPerView={'auto'}
                                coverflowEffect={{
                                    rotate: 0,
                                    stretch: 0,
                                    depth: 100,
                                    modifier: 2.5,
                                    slideShadows: false,
                                }}
                                navigation={{
                                    nextEl: '.swiper-button-next',
                                    prevEl: '.swiper-button-prev',
                                }}
                                pagination={{
                                    clickable: true,
                                    dynamicBullets: true,
                                }}
                                autoplay={{
                                    delay: 5000,
                                    disableOnInteraction: false,
                                    pauseOnMouseEnter: true
                                }}
                                breakpoints={{
                                    640: {
                                        coverflowEffect: {
                                            rotate: 0,
                                            stretch: 0,
                                            depth: 100,
                                            modifier: 2.5
                                        }
                                    },
                                    1024: {
                                        coverflowEffect: {
                                            rotate: 0,
                                            stretch: 0,
                                            depth: 150,
                                            modifier: 3
                                        }
                                    }
                                }}
                                className="swiper-container py-8"
                            >
                                {reviews.map((review) => (
                                    <SwiperSlide key={review._id} className="max-w-xs md:max-w-sm lg:max-w-md">
                                        <div className="h-full p-6 bg-gray-800/60 backdrop-blur-sm rounded-xl shadow-lg border border-gray-700/50 hover:border-blue-400/30 transition-all duration-300 transform hover:scale-[1.02]">
                                            <div className="flex items-center justify-between mb-4">
                                                <div>
                                                    <p className="font-bold text-lg text-blue-300">{review.fullName}</p>
                                                    <p className="text-gray-400 text-sm">{review.email}</p>
                                                </div>
                                                <div className="flex items-center space-x-1">
                                                    {[...Array(5)].map((_, i) => (
                                                        <svg
                                                            key={i}
                                                            className={`w-5 h-5 ${i < review.rating ? 'text-yellow-400' : 'text-gray-600'}`}
                                                            fill="currentColor"
                                                            viewBox="0 0 20 20"
                                                        >
                                                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                                        </svg>
                                                    ))}
                                                </div>
                                            </div>
                                            <h3 className="text-xl font-semibold mb-2 text-white">{review.reviewTitle}</h3>
                                            <p className="text-gray-300 mb-4 italic">"{review.comment}"</p>
                                            <div className="text-xs text-gray-500 text-right">
                                                {new Date(review.createdAt).toLocaleDateString()}
                                            </div>
                                        </div>
                                    </SwiperSlide>
                                ))}
                            </Swiper>

                            {/* Custom Navigation Arrows */}
                            <div className="swiper-button-prev !text-blue-400 !left-0"></div>
                            <div className="swiper-button-next !text-blue-400 !right-0"></div>
                        </div>
                    )}
                </section>

                {/* Review Form Section */}
                <section className="max-w-2xl mx-auto">
                    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 md:p-8 shadow-xl border border-gray-700/50">
                        <h3 className="text-2xl md:text-3xl font-bold text-center mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
                            Share Your Experience
                        </h3>
                        <p className="text-center text-gray-300 mb-6">
                            We value your feedback to help us improve
                        </p>

                        <div className="mb-6 bg-blue-900/20 border border-blue-700/50 rounded-lg p-4 text-center">
                            <div className="flex items-center justify-center mb-2">
                                <svg className="w-6 h-6 text-blue-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                                <span className="font-medium text-blue-300">Verified Buyer Reviews</span>
                            </div>
                            <p className="text-sm text-blue-200">
                                Only customers who have placed orders can submit reviews. 
                                This helps us maintain authentic feedback from real customers.
                            </p>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="grid md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="block text-gray-300 font-medium mb-2">Full Name</label>
                                    <input
                                        type="text"
                                        name="fullName"
                                        value={fullName}
                                        onChange={handleChange}
                                        readOnly
                                        className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition cursor-not-allowed"
                                    />
                                </div>
                                <div>
                                    <label className="block text-gray-300 font-medium mb-2">Email</label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={email}
                                        onChange={handleChange}
                                        readOnly
                                        className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition cursor-not-allowed"
                                    />
                                </div>
                            </div>

                            <div className="mb-4">
                                <label className="block text-gray-300 font-medium mb-2">Review Title</label>
                                <input
                                    type="text"
                                    name="reviewTitle"
                                    value={reviewTitle}
                                    onChange={handleChange}
                                    required
                                    className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                                    placeholder="Summarize your experience"
                                />
                            </div>

                            <div className="mb-4">
                                <label className="block text-gray-300 font-medium mb-2">Your Review</label>
                                <textarea
                                    name="comment"
                                    value={comment}
                                    onChange={handleChange}
                                    required
                                    rows="4"
                                    className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                                    placeholder="Tell us about your experience..."
                                ></textarea>
                            </div>

                            <div className="mb-6">
                                <label className="block text-gray-300 font-medium mb-2">Rating</label>
                                <div className="flex justify-center space-x-2">
                                    {[1, 2, 3, 4, 5].map((num) => (
                                        <button
                                            key={num}
                                            type="button"
                                            onClick={() => handleRatingClick(num)}
                                            className={`text-3xl transition-all duration-200 transform hover:scale-125 ${num <= rating ? "text-yellow-400" : "text-gray-500"}`}
                                        >
                                            ★
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all duration-300 ${isSubmitting
                                    ? 'bg-gray-600 cursor-not-allowed'
                                    : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg hover:shadow-blue-500/20'
                                    }`}
                            >
                                {isSubmitting ? (
                                    <span className="flex items-center justify-center">
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Submitting...
                                    </span>
                                ) : (
                                    'Submit Review'
                                )}
                            </button>
                        </form>
                    </div>
                </section>
            </div>
        </div>
    );
}

export default ReviewForm;