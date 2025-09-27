import React from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import CartItem from "../../components/OrderManagement/CartItem";
import Summary from "../../components/OrderManagement/Summary";

const ShoppingCart = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Retrieve cart items from Redux store
  const cartItems = useSelector((state) => state.cart.cartItems) || [];

  // Function to update quantity, ensuring it does not exceed stock
  const updateQuantity = (_id, quantity) => {
    console.log("Cart Items:", cartItems);
    const item = cartItems.find((item) => item._id === _id);
    if (item && quantity <= item.displayedStock) {
      dispatch({
        type: "UPDATE_CART_ITEM",
        payload: { _id, updates: { quantity } },
      });
    }
  };

  // Clear cart function
  const clearCart = () => {
    dispatch({ type: "CLEAR_CART" });
  };

  // Calculate total price directly from cart items
  const total = cartItems.reduce((acc, item) => {
    const price = item.discountPrice ? item.discountPrice : item.price;
    return acc + price * item.quantity;
  }, 0);

  return (
    <div className="container mx-auto p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Shopping Cart</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
      {/* /**
   * 
   * ToDo: This part got edited
   * 
   *  */}
   
        {/* Cart Items Section */}
        <div className="md:col-span-2 space-y-6">
          {cartItems.length > 0 ? (
            cartItems.map((item) => (
              <CartItem
                key={item._id}
                item={item}
                specs={item.specs}
                updateQuantity={updateQuantity}
              />

            ))
          ) : (
            <p>Your cart is empty.</p>
          )}

          {/* Cart Actions */}
          <div className="flex space-x-6 mt-6">
            <button
              className="bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700 focus:outline-none shadow-lg"
              onClick={clearCart}
            >
              Clear Shopping Cart
            </button>
            <button
              className="bg-gray-700 text-white py-2 px-4 rounded hover:bg-gray-800 focus:outline-none shadow-lg"
              onClick={() => (window.location.href = "/")}
            >
              Continue Shopping
            </button>
            <button
              className="bg-gray-700 text-white py-2 px-4 rounded hover:bg-gray-800 focus:outline-none shadow-lg"
              onClick={() => navigate("/OrderList")}
            >
              Orders
            </button>
          </div>
        </div>

        {/* Summary Section with Correct Total Calculation */}
        <div className="bg-gray-600 p-6 rounded-lg shadow-lg">
          <Summary cart={cartItems} total={total} />
        </div>

      </div>
    </div>
  );
};

export default ShoppingCart;
