import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';

const ProductCards = ({ products = [] }) => {
  const dispatch = useDispatch();
  // Retrieve the current cart items from the Redux store
  const cartItems = useSelector((state) => state.cart.cartItems) || [];
  // State to store the product ID of the recently added item (for confirmation message)
  const [addedToCartId, setAddedToCartId] = useState(null);

  // Check if a product is already in the cart by its _id
  const isProductInCart = (productId) => {
    return cartItems.some((item) => item._id === productId);
  };

  const handleAddToCart = (product) => {
    // If product is already in the cart, do nothing (or you can show a message)
    console.log("Adding product to cart:", product);
    if (isProductInCart(product._id)) return;

    const { _id, description, discountPrice, price, displayedStock, image } = product;
    // Use discounted price if available (and non-zero), otherwise use regular price.
    const effectivePrice = discountPrice ? discountPrice : price;

    dispatch({
      type: 'ADD_TO_CART',
      payload: { id: _id, description, price: effectivePrice, discountPrice, displayedStock, image, quantity: 1 },
    });

    // Set the product id to display the confirmation message
    setAddedToCartId(_id);
    // Clear the message after 2 seconds
    setTimeout(() => {
      setAddedToCartId(null);
    }, 2000);
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
      {products.map((product) => (
        <div key={product._id} className="product__card__content relative">
          <div className="relative">
            {/* Eye Icon - Positioned on top of the image */}
            <Link
              to={`/shop/${product._id}`}
              state={{ product }}
              className="absolute top-2 right-2 bg-pink-700 rounded-full p-2 hover:bg-pink-900 transition-colors z-10"
              onClick={() => window.scrollTo(0, 0)}
            >
              <i className="ri-eye-line text-xl text-white" title="View Details"></i>
            </Link>

            {/* Product Image */}
            <Link to={`/shop/${product._id}`} state={{ product }} className="relative block">
              <img
                src={product.image}
                alt={product.name}
                className="max-h-96 md:h-64 w-full object-cover transition-transform duration-300 hover:scale-105 p-3"
                onClick={() => window.scrollTo(0, 0)}
              />
            </Link>
          </div>
          
          {/* Product Details */}
          <div>
            <h4>{product.name}</h4>
            {product.description && (
              <p className="text-gray-900 text-xl pl-4 font-sans">
                {product.description}
              </p>
            )}
            <p className="text-sm text-gray-600 text-xl pl-5 pt-4">
              <span className="font-bold">LKR {product.discountPrice}</span>{' '}
              <s className="text-red-500">LKR {product.price}</s>
            </p>
          </div>

          {/* Add to Cart Button */}
          <div className="hover:block m-5">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleAddToCart(product);
              }}
              // Disable button if product is already in cart
              disabled={isProductInCart(product._id)}
              className={`${
                isProductInCart(product._id) ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <i className="ri-shopping-cart-line bg-black text-white hover:bg-primary-dark p-3 m-8 rounded-3xl align-middle ml-11"></i>
            </button>
          </div>

          {/* Confirmation Message */}
          {addedToCartId === product._id && (
            <div className="absolute top-0 right-0 bg-green-500 text-white py-1 px-2 rounded shadow-md">
              Added to cart!
            </div>
          )}

          {/* Optional: Message for already added products */}
          {isProductInCart(product._id) && !addedToCartId && (
            <div className="absolute top-0 right-0 bg-gray-700 text-white py-1 px-2 rounded shadow-md">
              Already in cart
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ProductCards;