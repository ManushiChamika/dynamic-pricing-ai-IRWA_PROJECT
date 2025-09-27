import React from "react";
import "../../styles/OrderManagement/PickupForm.css"; // Make sure to create this CSS file

const PickupForm = ({ pickupData, handlePickupChange }) => {
  const timeSlots = [
    "9:00 AM - 11:00 AM",
    "11:00 AM - 1:00 PM",
    "2:00 PM - 4:00 PM",
    "4:00 PM - 6:00 PM",
    "6:00 PM - 8:00 PM",
  ];
  
  return (
    <div className="pickup-form">
      <h4>Pick-Up (Self Collect) Details</h4>

      <div className="form-group">
        <label>Pickup Date</label>
        <input
          type="date"
          name="pickupDate"
          value={pickupData.pickupDate}
          onChange={handlePickupChange}
          required
        />
      </div>

      <div className="form-group">
        <label>Pickup Time</label>
        <select
          type="time"
          name="pickupTime"
          value={pickupData.pickupTime}
          onChange={handlePickupChange}
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

export default PickupForm;
