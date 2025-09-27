const initialState = {
  cartItems: [],
};

const cartReducer = (state = initialState, action) => {
  switch (action.type) {
    case "ADD_TO_CART":
      console.log("Adding item to cart:", action.payload);
      const payloadId = action.payload.id || action.payload._id;
      const existingItemIndex = state.cartItems.findIndex(
        (item) => item.id === payloadId || item._id === payloadId
      );


      if (existingItemIndex !== -1) {
        // If item exists, update its quantity
        const updatedCartItems = [...state.cartItems];
        updatedCartItems[existingItemIndex] = {
          ...updatedCartItems[existingItemIndex],
          quantity: updatedCartItems[existingItemIndex].quantity + (action.payload.quantity || 1),
        };
        // return {
        //   ...state,
        //   cartItems: updatedCartItems,
        // };

        // Dispatch the API call to save the item to the order table
        saveToOrderDatabase(action.payload._id);
        return {
          ...state,
          cartItems: updatedCartItems,
        };
      } else {
        // If item doesn't exist, add to cart
        return {
          ...state,
          cartItems: [...state.cartItems, { ...action.payload, quantity: action.payload.quantity || 1 }],
        };
      }

    case "UPDATE_CART_ITEM":
      console.log("Updating item with ID:", action.payload._id, "to quantity:", action.payload.updates.quantity);
      return {
        ...state,
        cartItems: state.cartItems.map((item) =>
          item._id === action.payload._id
            ? { ...item, quantity: action.payload.updates.quantity }
            : item
        ),
      };

    case "CLEAR_CART":
      return { ...state, cartItems: [] };

    default:
      return state;
  }
};

// Function to save the item to the successOrder table
const saveToOrderDatabase = async (itemId) => {
  try {
    const response = await axios.post('/api/successorders/create', { itemId });  // Adjust the API endpoint as needed
    console.log('SuccessOrder saved successfully:', response.data);
  } catch (error) {
    console.error('Error saving order:', error);
  }
};

export default cartReducer;