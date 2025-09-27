import React from "react";
import "../../styles/OrderManagement/CodForm.css";

const CodForm = ({ codData, handleCodChange }) => {
  const timeSlots = [
    "9:00 AM - 11:00 AM",
    "11:00 AM - 1:00 PM",
    "2:00 PM - 4:00 PM",
    "4:00 PM - 6:00 PM",
    "6:00 PM - 8:00 PM",
  ];
  
  return (
    <div className="cod-form">
      <h4>Cash On Delivery (COD) Details</h4>
      
      <div className="form-group">
        <label>Address</label>
        <input
          type="text"
          name="address"
          value={codData.address}
          onChange={handleCodChange}
          required
          placeholder="Enter delivery address"
        />
      </div>

      <div className="form-group">
        <label>Pickup Date</label>
        <input
          type="date"
          name="deliveryDate"
          value={codData.deliveryDate}
          onChange={handleCodChange}
          required
        />
      </div>

      <div className="form-group">
        <label>Pickup Time</label>
        <select
          type="time"
          name="deliveryTime"
          value={codData.deliveryTime}
          onChange={handleCodChange}
          required
        >
          <option value="">Select a time slot</option>
          {timeSlots.map((slot, index) => (
            <option key={index} value={slot}>{slot}</option>
          ))}  
        </select>
      </div>
    </div>
  );
};

export default CodForm;
