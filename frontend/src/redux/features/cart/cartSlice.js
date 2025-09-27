import { createSlice } from '@reduxjs/toolkit';
import { v4 as uuidv4 } from 'uuid'; // Make sure to install this with: npm install uuid

const initialState = {
    products: [],
    selectedItems: 0,
    totalPrice: 0,
    tax: 0,
    taxRate: 0.05,
    grandTotal: 0,
    customerOrders: [], // array of past orders
};

const cartSlice = createSlice({
    name: 'cart',
    initialState,
    reducers: {
        addToCart: (state, action) => {
            // Assign a unique cartId to each added item
            const newItem = {
                ...action.payload,
                cartId: uuidv4(),
                quantity: 1,
                specs: action.payload.specs || [],   // ← default to empty array
            };

            state.products.push(newItem);

            // Recalculate totals
            state.selectedItems = setSelectedItems(state);
            state.totalPrice = setTotalPrice(state);
            state.tax = setTax(state);
            state.grandTotal = setGrandTotal(state);
        },

        updateQuantity: (state, action) => {
            state.products = state.products.map((product) => {
                if (product.cartId === action.payload.cartId) {
                    if (action.payload.type === 'increment') {
                        product.quantity += 1;
                    } else if (action.payload.type === 'decrement' && product.quantity > 1) {
                        product.quantity -= 1;
                    }
                }
                return product;
            });

            // Recalculate totals
            state.selectedItems = setSelectedItems(state);
            state.totalPrice = setTotalPrice(state);
            state.tax = setTax(state);
            state.grandTotal = setGrandTotal(state);
        },

        removeFromCart: (state, action) => {
            state.products = state.products.filter(
                (product) => product.cartId !== action.payload.cartId
            );

            // Recalculate totals
            state.selectedItems = setSelectedItems(state);
            state.totalPrice = setTotalPrice(state);
            state.tax = setTax(state);
            state.grandTotal = setGrandTotal(state);
        },

        clearCart: (state) => {
            state.products = [];
            state.selectedItems = 0;
            state.totalPrice = 0;
            state.tax = 0;
            state.grandTotal = 0;
        },
        addOrder: (state, action) => {
            state.customerOrders.push({
                id: uuidv4(),
                date: new Date().toLocaleString(),
                items: [...state.products],
                total: state.grandTotal,
            });
        
            // Optional: Clear cart after placing order
            state.products = [];
            state.selectedItems = 0;
            state.totalPrice = 0;
            state.tax = 0;
            state.grandTotal = 0;
        },        
    },
});

// Utility functions for recalculation
export const setSelectedItems = (state) =>
    state.products.reduce((total, product) => total + product.quantity, 0);

export const setTotalPrice = (state) =>
    state.products.reduce((total, product) => total + product.quantity * product.price, 0);

export const setTax = (state) => setTotalPrice(state) * state.taxRate;

export const setGrandTotal = (state) => setTotalPrice(state) + setTax(state);

// Export actions
export const { addToCart, updateQuantity, removeFromCart, clearCart, addOrder } = cartSlice.actions;
export default cartSlice.reducer;
