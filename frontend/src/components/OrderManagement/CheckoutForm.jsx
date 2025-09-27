import { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation, useSearchParams } from "react-router-dom";
import axios from "axios";
import PickupForm from "./pickupForm";
import CodForm from "./CodForm";
import { deleteOrder, updateOrder } from "./orderService";
import "../../styles/OrderManagement/CheckoutForm.css";

const CheckoutForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // For state
  const location = useLocation();
  const editMode = location.state?.editMode;
  
  const timeSlots = [
    "9:00 AM - 11:00 AM",
    "11:00 AM - 1:00 PM",
    "2:00 PM - 4:00 PM",
    "4:00 PM - 6:00 PM",
    "6:00 PM - 8:00 PM",
  ];
  const [formData, setFormData] = useState({
    name: "",
    phoneNo: "",
    email: "",
    paymentMethod: "COD",
  });
  const [codData, setCodData] = useState({
    address: "",
    deliveryDate: "",
    deliveryTime: "",
    saveAddress: false,
  });
  const [pickupData, setPickupData] = useState({
    pickupDate: "",
    pickupTime: "",
  });

  const [successOrder, setSuccessOrder] = useState(null);
  const [canModify, setCanModify] = useState(true);

  useEffect(() => {
    const savedOrder = localStorage.getItem("successOrder");
    if (savedOrder) {
      const parsedOrder = JSON.parse(savedOrder);
      setSuccessOrder(parsedOrder);
  
      const order = parsedOrder.order;

      setFormData({
        name: order.name,
        phoneNo: order.phoneNo,
        email: order.email,
        paymentMethod: order.paymentMethod,
      });

      if (order.paymentMethod === "COD") {
        setCodData({
          address: order.codDetails.address,
          deliveryDate: order.codDetails.deliveryDate,
          deliveryTime: order.codDetails.deliveryTime,
          saveAddress: order.codDetails.saveAddress || false,
        });
      } else {
        setPickupData({
          pickupDate: order.pickupDetails.pickupDate,
          pickupTime: order.pickupDetails.pickupTime,
        });
      }
  
      checkTimeLimit(order);
    } else if (id) {
      axios
        .get(`http://localhost:5000/api/orders/${id}`)
        .then((response) => {
          const order = response.data;
          setSuccessOrder(order);
          localStorage.setItem("successOrder", JSON.stringify(order));
          setFormData({
            // id: order._id,
            name: order.name,
            phoneNo: order.phoneNo,
            email: order.email,
            paymentMethod: order.paymentMethod,
          });

          if (order.paymentMethod === "COD") {
            setCodData({
              address: order.address,
              deliveryDate: order.deliveryDate,
              deliveryTime: order.deliveryTime,
              saveAddress: order.saveAddress || false,
            });
          } else {
            setPickupData({
              pickupDate: order.pickupDate,
              pickupTime: order.pickupTime,
            });
          }

          checkTimeLimit(order);
        })
        .catch((error) => {
          console.error("Error fetching order:", error);
        });
    }
  }, [id]);

  const checkTimeLimit = (order) => {
    if (!order) return;
    const orderTime = new Date(order.createdAt);
    const currentTime = new Date();
    const diffHours = (currentTime - orderTime) / (1000 * 60 * 60);
    setCanModify(diffHours <= 24);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCodChange = (e) => {
    setCodData({ ...codData, [e.target.name]: e.target.value });
  };

  const handlePickupChange = (e) => {
    setPickupData({ ...pickupData, [e.target.name]: e.target.value });
  };

  const handlePaymentChange = (e) => {
    const selectedMethod = e.target.value;

    setFormData({ ...formData, paymentMethod: selectedMethod });

    if (selectedMethod === "Pickup") {
      setPickupData({
        pickupDate: "",
        pickupTime: "",
      });
    } else if (selectedMethod === "COD") {
      setCodData({
        address: "",
        deliveryDate: "",
        deliveryTime: "",
        saveAddress: false,
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const orderData = {
      ...formData,
      ...(formData.paymentMethod === "COD" ? codData : pickupData),
    };

    const token = localStorage.getItem("token"); // ⬅️ Get the token from storage

    if (!token) {
      alert("You must be logged in to place an order.");
      navigate("/login");
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:5000/api/orders/create",
        orderData,
        {
          headers: {
            Authorization: `Bearer ${token}`, // ⬅️ Add token here
          },
        }
      );
      // setSuccessOrder(response.data);
      setSuccessOrder(response.data);
      localStorage.setItem("successOrder", JSON.stringify(response.data));
      
      alert("Order placed successfully!");
      localStorage.setItem("orderPlaced", "true");
    } catch (error) {
      console.error(
        "Error placing order:",
        error.response?.data || error.message
      );
      alert("Failed to place order. Please check your details and try again.");
    }
  };

  // useEffect(() => {
  //   if (successOrder) {
  //     console.log("Order after placement:", successOrder);
  //   }
  // }, [successOrder]);

  useEffect(() => {
    if (editMode) {
      setSuccessOrder(true);
      setCanModify(true);
    }
  }, [editMode]);
  
  const handleUpdate = async () => {
    console.log("Updating Order ID:", successOrder.order._id);
    const confirmUpdate = window.confirm("Are you sure you want to update this order?");
    if (!confirmUpdate) return;

    let updatedOrderData = {
      ...formData,
      // ...(formData.paymentMethod === "COD" ? codData : pickupData),
    };

    if (formData.paymentMethod === "COD") {
      updatedOrderData = {
        ...updatedOrderData,
        codDetails: { ...codData },
        pickupDetails: undefined, // remove pickupDetails if it exists
      };
    } else if (formData.paymentMethod === "Pickup") {
      updatedOrderData = {
        ...updatedOrderData,
        pickupDetails: { ...pickupData },
        codDetails: undefined, // remove codDetails if it exists
      };
    }

    try {
      const result = await updateOrder(successOrder.order._id, updatedOrderData);
      alert(result.message || "Order updated successfully!");
      // setSuccessOrder({ ...successOrder, ...updatedOrderData });
      setSuccessOrder({ ...successOrder, order: { ...successOrder.order, ...updatedOrderData } });
      localStorage.setItem("successOrder", JSON.stringify({
        order: { ...successOrder.order, ...updatedOrderData }
      }));

    } catch (error) {
      console.error("Error updating order:", error);
      alert("Failed to update order.");
    }
  };

  const handleDelete = async () => {
    console.log("Deleting Order ID:", successOrder.order._id);
    if (!successOrder?.order._id) {
      alert("Order not found. Id is required.");
      return;
    }
  
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this order?"
    );
    if (!confirmDelete) return;
  
    try {
      const result = await deleteOrder(successOrder.order._id);
      alert(result.message || "Order deleted successfully!");
      setSuccessOrder(null);
      localStorage.removeItem("successOrder");

      navigate("/shoppingcart");
    } catch (error) {
      console.error("Error deleting order:", error);
      alert("Failed to delete order.");
    }
  };  

  return (
    <div className="form-container">
      <h2 className="header">Checkout</h2>
      {!successOrder/* || !localStorage.getItem("orderPlaced")*/ ? (
        <form className="form" onSubmit={handleSubmit}>
          <label className="label">Full Name</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="input"
          />

          <label className="label">Phone Number</label>
          <input
            type="text"
            name="phoneNo"
            value={formData.phoneNo}
            onChange={handleChange}
            required
            className="input"
          />

          <label className="label">Email Address</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="input"
          />

          <h3 className="header">Payment Options</h3>
          <label className="radio-label">
            <input
              type="radio"
              name="paymentMethod"
              value="COD"
              checked={formData.paymentMethod === "COD"}
              onChange={handleChange}
            />
            Cash On Delivery
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="paymentMethod"
              value="Pickup"
              checked={formData.paymentMethod === "Pickup"}
              onChange={handleChange}
            />
            Pick-Up (Self Collect)
          </label>

          {formData.paymentMethod === "Pickup" && (
            <PickupForm
              pickupData={pickupData}
              handlePickupChange={handlePickupChange}
            />
          )}
          {formData.paymentMethod === "COD" && (
            <CodForm codData={codData} handleCodChange={handleCodChange} />
          )}

          <button type="submit" className="submit-button">
            Save and Place Order
          </button>
        </form>
      ) : (
        <div className="success-order-container">
          <h3 className="success-header">Order Successfully Placed!</h3>
          <p>Thank you for your order. Here are the details:</p>
          <ul className="order-details">
            <li>
              <strong>Name:</strong> {formData.name}
            </li>
            <li>
              <strong>Phone No:</strong> {formData.phoneNo}
            </li>
            <li>
              <strong>Email:</strong> {formData.email}
            </li>
            <li>
              <strong>Order Type:</strong>{" "}
              {formData.paymentMethod === "COD"
                ? "Cash On Delivery"
                : "Pickup (Self Collect)"}
            </li>
            {formData.paymentMethod === "COD" && (
              <>
                <li>
                  <strong>Address:</strong> {codData.address}
                </li>
                <li>
                  <strong>Delivery Date:</strong> {codData.deliveryDate}
                </li>
                <li>
                  <strong>Delivery Time:</strong> {codData.deliveryTime}
                </li>
              </>
            )}
            {formData.paymentMethod === "Pickup" && (
              <>
                <li>
                  <strong>Pickup Date:</strong> {pickupData.pickupDate}
                </li>
                <li>
                  <strong>Pickup Time:</strong> {pickupData.pickupTime}
                </li>
              </>
            )}
          </ul>

          <button className="delete-button" onClick={() => handleDelete()}>
            Delete
          </button>
        </div>
      )}

      {successOrder && canModify && (
        <div className="order-details-container">
          <h2 className="header">Order Details</h2>
          <div>
            <div className="input-group">
              <strong className="label">Full Name:</strong>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="edit-input"
              />
            </div>
            <div className="input-group">
              <strong className="label">Phone Number:</strong>
              <input
                type="text"
                name="phoneNo"
                value={formData.phoneNo}
                onChange={handleChange}
                className="edit-input"
              />
            </div>
            <div className="input-group">
              <strong>Email:</strong>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="edit-input"
              />
            </div>
            <div className="input-group">
              <strong>Payment Method:</strong>
              <select
                name="paymentMethod"
                value={formData.paymentMethod}
                onChange={handlePaymentChange}
                className="edit-input"
              >
                <option value="COD">Cash On Delivery</option>
                <option value="Pickup">Pick-Up (Self Collect)</option>
              </select>
            </div>
            {formData.paymentMethod === "COD" && (
              <>
                <div className="input-group">
                  <strong>Delivery Address:</strong>
                  <input
                    type="text"
                    name="address"
                    value={codData.address}
                    onChange={handleCodChange}
                    className="edit-input"
                  />
                </div>
                <div className="input-group">
                  <strong>Delivery Date:</strong>
                  <input
                    type="date"
                    name="deliveryDate"
                    value={codData.deliveryDate}
                    onChange={handleCodChange}
                    className="edit-input"
                  />
                </div>
                <div className="input-group">
                  <strong>Delivery Time:</strong>
                  <select
                    type="time"
                    name="deliveryTime"
                    value={codData.deliveryTime}
                    onChange={handleCodChange}
                    className="edit-input"
                  >
                    <option value="">Select a time slot</option>
                    {timeSlots.map((slot, index) => (
                      <option key={index} value={slot}>{slot}</option>
                    ))}
                  </select>
                </div>
              </>
            )}
            {formData.paymentMethod === "Pickup" && (
              <>
                <div className="input-group">
                  <strong>Pickup Date:</strong>
                  <input
                    type="date"
                    name="pickupDate"
                    value={pickupData.pickupDate}
                    onChange={handlePickupChange}
                    className="edit-input"
                  />
                </div>
                <div className="input-group">
                  <strong>Pickup Time:</strong>
                  <select
                    type="time"
                    name="pickupTime"
                    value={pickupData.pickupTime}
                    onChange={handlePickupChange}
                    className="edit-input"
                  >
                    <option value="">Select a time slot</option>
                    {timeSlots.map((slot, index) => (
                      <option key={index} value={slot}>{slot}</option>
                    ))}
                    </select>
                </div>
              </>
            )}
            <div>
              <button
                className="save-button"
                onClick={() => handleUpdate()}
              >
                Save Changes
              </button>
            </div>
            <button
              className="cart-button"
              onClick={() => navigate("/shoppingcart")}
              style={{
                backgroundColor: "#3498db",
                color: "white",
                padding: "10px 20px",
                marginTop: "10px",
                border: "none",
                borderRadius: "8px",
                fontSize: "16px",
                cursor: "pointer",
                boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                transition: "background-color 0.3s"
              }}
            >
              Go to Shopping Cart
            </button>

          </div>
        </div>
      )}
    </div>
  );
};

export default CheckoutForm;
