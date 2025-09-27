// index.js (or your main entry file)
import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import store, { persistor } from "./redux/store"; 
import { RouterProvider } from "react-router-dom";
import './index.css';
import { AuthProvider } from "../src/context/authContext";
import router from "./routers/Router";
import { PersistGate } from "redux-persist/integration/react";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </PersistGate>
    </Provider>
  </React.StrictMode>
);
