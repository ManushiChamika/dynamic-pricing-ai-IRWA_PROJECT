import React, { useState, useEffect } from "react";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";
import axios from "axios";
import { Button } from "./ui";
import "../../styles/appointment.css";
import { useAuth } from "../../context/authContext";

const timeSlots = ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM"];

const Input = ({ value, onChange, placeholder, type = "text", required = false, className = "", pattern, title, ...props }) => (
  <input
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    type={type}
    required={required}
    pattern={pattern}
    title={title}
    className={`w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-600 focus:ring focus:ring-blue-500 ${className}`}
    {...props}
  />
);

export default function AppointmentDashboard() {
  const { user } = useAuth();
  const [date, setDate] = useState(new Date());
  const [selectedTime, setSelectedTime] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
    deviceType: "",
    issueDescription: "",
    contactMethod: "email",
    problemType: "",
    pickupOrDropoff: "",
    chipLevelRepair: false,
    attemptedFixes: false,
    backupData: false,
  });
  const [isBooked, setIsBooked] = useState(false);
  const [errors, setErrors] = useState({});
  const [bookingError, setBookingError] = useState("");

  useEffect(() => {
    if (user) {
      setFormData(prev => ({
        ...prev,
        name: user.name || "",
        email: user.email || "",
        phone: user.phone || user.contactNumber || "",
        address: user.address || ""
      }));
    }
  }, [user]);

  const validators = {
    name: {
      pattern: /^[A-Za-z\s]{2,50}$/,
      message: "Name must only contain letters and be 2-50 characters long."
    },
    email: {
      pattern: /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/,
      message: "Invalid email format."
    },
    phone: {
      pattern: /^\d{10}$/,
      message: "Phone number must be exactly 10 digits."
    },
  };

  const handleInputChange = (key, value) => {
    setFormData(prev => ({
      ...prev,
      [key]: value,
    }));

    if (validators[key]) {
      const { pattern, message } = validators[key];
      if (!pattern.test(value)) {
        setErrors(prev => ({ ...prev, [key]: message }));
      } else {
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors[key];
          return newErrors;
        });
      }
    }
  };

  const formatDateLocal = (dateObj) => {
    const tzOffset = dateObj.getTimezoneOffset() * 60000;
    return new Date(dateObj.getTime() - tzOffset).toISOString().split("T")[0];
  };

  const handleBooking = async () => {
    setBookingError("");

    if (Object.keys(errors).length > 0) {
      setBookingError("Please match the requested format");
      return;
    }

    if (!formData.address) {
      setBookingError("Address is required");
      return;
    }

    if (formData.name && formData.email && selectedTime) {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://localhost:5000/api/appointments",
          {
            ...formData,
            userId: user._id,
            date: formatDateLocal(date),
            timeSlot: selectedTime,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.status === 201) {
          setIsBooked(true);
          setBookingError("");
        }
      } catch (error) {
        if (error.response && error.response.status === 400) {
          setBookingError(error.response.data.message);
        } else {
          console.error("Error booking appointment:", error);
          setBookingError("An unexpected error occurred. Please try again.");
        }
      }
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-black to-gray-900 text-white">
      <header className="bg-gradient-to-r from-red-600 to-blue-600 text-white py-4 text-center shadow-lg">
        <h1 className="text-3xl font-bold">Computer Repair Appointment Booking</h1>
      </header>
      <main className="flex-grow p-6 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Calendar */}
          <div className="p-6 rounded-lg shadow-lg border border-gray-700 bg-gray-900 bg-opacity-90">
            <h2 className="text-xl font-semibold mb-4">Select a Date</h2>
            <Calendar
              onChange={setDate}
              value={date}
              minDate={new Date()}
              maxDate={new Date(new Date().setFullYear(new Date().getFullYear() + 1))}
              className="custom-calendar"
            />
            <p className="mt-2 text-sm text-gray-400">Only appointments up to one year in advance can be booked.</p>
          </div>

          {/* Time Slots */}
          <div className="p-6 rounded-lg shadow-lg border border-gray-700 bg-gray-900 bg-opacity-90">
            <h2 className="text-xl font-semibold mb-4">Select a Time Slot</h2>
            <div className="grid grid-cols-2 gap-3">
              {timeSlots.map((slot) => (
                <Button
                  key={slot}
                  variant={selectedTime === slot ? "default" : "outline"}
                  onClick={() => setSelectedTime(slot)}
                  className={`rounded-lg p-3 transition-all ${
                    selectedTime === slot
                      ? "bg-gradient-to-r from-red-600 to-blue-600 text-white"
                      : "bg-white text-black"
                  }`}
                >
                  {slot}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Form Fields */}
        <div className="mt-6 p-6 rounded-lg shadow-lg border border-gray-700 bg-gray-900 bg-opacity-90">
          <h2 className="text-xl font-semibold mb-4">Enter Your Details</h2>

          {[
            { label: "Full Name", key: "name", required: true, type: "text" },
            { label: "Email", key: "email", required: true, type: "email" },
            { label: "Phone Number", key: "phone", required: true, type: "tel" },
            { label: "Address", key: "address", required: true, type: "text" },
            { label: "Device Type", key: "deviceType", required: true, type: "text" },
            { label: "Issue Description", key: "issueDescription", required: true, type: "text" },
          ].map(({ label, key, required, type }) => (
            <div className="mb-4" key={key}>
              <label className="block text-sm font-medium">
                {label} {required && <span className="text-red-500">*</span>}
              </label>
              <Input
                value={formData[key]}
                placeholder={label}
                onChange={(e) => handleInputChange(key, e.target.value)}
                type={type}
                required={required}
              />
              {errors[key] && <p className="text-red-500 text-sm">{errors[key]}</p>}
            </div>
          ))}

          {/* Dropdowns */}
          {[
            { label: "Preferred Contact Method", key: "contactMethod", options: ["email", "phone"] },
            { label: "Problem Type", key: "problemType", options: ["", "hardware", "software", "virus"] },
            { label: "Pickup or Dropoff", key: "pickupOrDropoff", options: ["", "pickup", "dropoff"] },
          ].map(({ label, key, options }) => (
            <div className="mb-4" key={key}>
              <label className="block text-sm font-medium">{label} <span className="text-red-500">*</span></label>
              <select
                className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-600"
                value={formData[key]}
                onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
                required
              >
                {options.map(opt => (
                  <option value={opt} key={opt}>
                    {opt ? opt.charAt(0).toUpperCase() + opt.slice(1) : "Select Option"}
                  </option>
                ))}
              </select>
            </div>
          ))}

          {/* Checkboxes */}
          {[
            { label: "Chip-Level Repair Required", key: "chipLevelRepair" },
            { label: "Have You Attempted Any Fixes?", key: "attemptedFixes" },
            { label: "Do You Need Data Backup Before Repairs?", key: "backupData" },
          ].map(({ label, key }) => (
            <div className="mb-4" key={key}>
              <label className="block text-sm font-medium">
                <input
                  type="checkbox"
                  checked={formData[key]}
                  onChange={(e) => setFormData({ ...formData, [key]: e.target.checked })}
                  className="mr-2"
                />
                {label}
              </label>
            </div>
          ))}

          <Button
            className="w-full p-3 rounded-lg bg-gradient-to-r from-red-600 to-blue-600 text-white font-semibold transition-all hover:from-red-700 hover:to-blue-700"
            onClick={handleBooking}
          >
            Book Appointment
          </Button>
        </div>

        {/* Feedback */}
        {bookingError && (
          <div className="mt-6 p-6 rounded-lg bg-red-500 text-white text-center">
            <p>{bookingError}</p>
          </div>
        )}
        {isBooked && (
          <div className="mt-6 p-6 rounded-lg bg-green-500 text-white text-center">
            <h2 className="text-xl font-semibold">Appointment Confirmed!</h2>
            <p>Your appointment for <strong>{formData.deviceType}</strong> repair is booked for <strong>{date.toDateString()}</strong> at <strong>{selectedTime}</strong>.</p>
            <p>We will contact you via <strong>{formData.contactMethod}</strong>.</p>
            <p>Address: <strong>{formData.address}</strong></p>
          </div>
        )}
      </main>
    </div>
  );
}
