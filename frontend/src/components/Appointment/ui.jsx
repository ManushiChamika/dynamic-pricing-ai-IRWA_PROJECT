import React from "react";

// Button Component
export function Button({ children, variant = "default", onClick }) {
  const baseStyles = "px-4 py-2 rounded-lg font-semibold transition-all";
  const variantStyles = variant === "default" ? "bg-blue-500 text-white" : "border border-gray-300 text-gray-700";
  return (
    <button className={`${baseStyles} ${variantStyles}`} onClick={onClick}>{children}</button>
  );
}

// Input Component
export function Input({ placeholder, className, onChange }) {
  return (
    <input
      type="text"
      placeholder={placeholder}
      className={`w-full px-3 py-2 border rounded-lg ${className}`}
      onChange={onChange}
    />
  );
}

// Card Component
export function Card({ children }) {
  return <div className="border rounded-lg shadow-lg overflow-hidden">{children}</div>;
}

// Card Content Component
export function CardContent({ children, className }) {
  return <div className={`p-4 ${className}`}>{children}</div>;
}