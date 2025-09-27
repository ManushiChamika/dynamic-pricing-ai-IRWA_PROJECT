import React from 'react';
import { Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';

const ProductList = ({ products }) => {
  const dispatch = useDispatch();

  const handleAddToCart = (product) => {
    dispatch({ type: 'ADD_TO_CART', payload: product });
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
      {products.map((product, index) => (
        <div key={index} className="product__card__content relative border p-4">
          <div className="relative">
            {/* Passing the entire product as state */}
            <Link to={`/shop/${product._id}`} state={{ product }}>
              <img
                src={product.image}
                alt="Product Image"
                className="max-h-96 md:h-64 w-full object-cover hover:scale-105 transition-all duration-300 p-3"
                onClick={() => window.scrollTo(0, 0)} // Scrolls to top when clicked
              />
            </Link>
            <Link
              to={`/shop/${product._id}`}
              state={{ product }}
              className="absolute top-2 right-2 text-white bg-pink-700 rounded-full p-2 hover:bg-pink-900 transition-colors"
              onClick={() => window.scrollTo(0, 0)} // Scrolls to top when clicked
            >
              <i className="ri-eye-line text-xl" title="View Details"></i>
            </Link>
          </div>
          <div>
            {product.description && (
              <p className="text-gray-900 text-xl pl-4 font-sans">{product.description}</p>
            )}
            <p className="text-sm text-gray-600 text-xl pl-5 pt-4">
              {product.price === product.discountPrice ? (
                <span className="font-bold">LKR {product.price}</span>
              ) : (
                <>
                  <span className="font-bold">LKR {product.discountPrice}</span>{' '}
                  <s className="text-red-500">LKR {product.price}</s>
                </>
              )}
            </p>
          </div>
          <div className="hover:block m-5">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleAddToCart(product);
              }}
            >
              <i className="ri-shopping-cart-line bg-black text-white hover:bg-primary-dark p-3 m-8 rounded-3xl align-middle ml-11"></i>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProductList;
