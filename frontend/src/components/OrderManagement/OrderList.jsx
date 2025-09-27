import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { deleteOrder, updateOrder } from "./orderService";

const OrderStatusBadge = ({ status }) => {
  const statusStyles = {
    Pending: "bg-yellow-200 text-yellow-800",
    Approved: "bg-blue-200 text-blue-800",
    Cancelled: "bg-red-200 text-red-800",
    handedOver: "bg-green-200 text-green-800",
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${statusStyles[status] || "bg-gray-300 text-gray-700"}`}>
      {status}
    </span>
  );
};

const OrderList = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const token = localStorage.getItem("token");
        
        const successRes = await axios.get("http://localhost:5000/api/successorders/successOrder/all", {
          headers: {
            Authorization: `Bearer ${token}`,
            "Cache-Control": "no-cache",
          },
        });
        const successOrders = Array.isArray(successRes.data) ? successRes.data : [successRes.data];
    
        const ordersRes = await axios.get("http://localhost:5000/api/orders/all", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const allOrders = Array.isArray(ordersRes.data) ? ordersRes.data : [ordersRes.data];
    
        const detailedOrders = successOrders.map((sOrder) => {
          const matchedOrder = allOrders.find(order => 
            order.SuccessorderId && order.SuccessorderId._id === sOrder._id
          );
          return matchedOrder ? { ...sOrder, details: matchedOrder } : null;
        }).filter(Boolean);
    
        console.log("Detailed orders with match:", detailedOrders);
        setOrders(detailedOrders);
      } catch (error) {
        console.error("Error fetching orders", error);
      } finally {
        setLoading(false);
      }
    };
  
    fetchOrders();
  }, []);  
  

  const handleDelete = async (orderId) => {
    if (!window.confirm("Are you sure you want to delete this order info?")) return;

    const result = await deleteOrder(orderId);
    if (result && result.message !== "Error deleting order") {
      setOrders((prevOrders) => prevOrders.filter((order) => order.details._id !== orderId));
    } else {
      alert("Failed to delete the order.");
    }
  };

  const getItemRoute = (item) => {
    switch (item.itemType.toLowerCase()) {
      case "prebuild":
        return `/gaming-builds/${item.itemId._id}`;
      case "product":
        return `/shop/${item.itemId._id}`;
      default:
        return "/";
    }
  };

  if (loading) return <p className="text-center text-gray-600">Loading orders...</p>;

  if (!orders.length) return <p className="text-center text-gray-600">No orders found.</p>;

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-6">My Orders</h2>

      {orders.map((order) => (
        <div key={order._id} className="border rounded-lg p-4 mb-6 shadow-md">
          <div className="flex justify-between items-center mb-2">
            <OrderStatusBadge status={order.status} />
            <span className="text-sm text-gray-500">
              Ordered At: {new Date(order.createdAt).toLocaleString()}
            </span>
          </div>

          <p className="text-lg font-semibold mb-2">Total: LKR {order.totalAmount}</p>

          <div className="mt-3">
            <strong>Items:</strong>
            <ul className="list-none space-y-4 mt-3">
              {order.items.map((item, idx) => (
                <li key={idx} className="flex justify-between items-start bg-white shadow-md rounded-lg p-4">
                 <div className="flex items-center space-x-4">
                  {item.itemId?.image && (
                    <img
                    src={item.itemId.image}
                    alt="item"
                    className="w-16 h-16 object-cover rounded-md"
                    onError={(e) => (e.target.style.display = "none")}
                    />
                  )}
                <div className="flex flex-col">
                  <span className="text-lg font-semibold">
                    {item.itemType}: {item.itemId?.description || "Unnamed"} x {item.quantity}
                  </span>
                </div>
                
                </div>
        
              {/* Show specs for PreBuild items */}
              {item.itemType === 'PreBuild' && item.specs && item.specs.length > 0 && (
                <div className="mt-4 text-sm text-gray-700">
                  <p className="font-medium text-gray-800">Specs:</p>
                  <ul className="space-y-1">
                    {item.specs.map((spec, idx) => (
                      <li key={idx} className="flex space-x-2">
                        <span className="font-semibold text-gray-600">{spec.label}:</span>
                        <span>{spec.value}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
        
              {/* View Item button */}
              {item.itemId?._id && (
                <div className="mt-4">
                  <button
                    onClick={() => navigate(getItemRoute(item))}
                    className="bg-blue-500 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-600 transition-all"
                  >
                    View Item
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
        
          </div>

          {order.details && (
            <div className="mt-4">
              <h3 className="font-semibold mb-1">Customer Info:</h3>
              <p><strong>Name:</strong> {order.details.name}</p>
              <p><strong>Phone:</strong> {order.details.phoneNo}</p>
              <p><strong>Email:</strong> {order.details.email}</p>
              <p><strong>Payment Method:</strong> {order.details.paymentMethod}</p>

              {order.details.paymentMethod === "COD" ? (
                <>
                  <p><strong>Delivery Address:</strong> {order.details.codDetails?.address}</p>
                  <p><strong>Delivery Time:</strong> {order.details.codDetails?.deliveryDate} at {order.details.codDetails?.deliveryTime}</p>
                </>
              ) : (
                <>
                  <p><strong>Pickup Date:</strong> {order.details.pickupDetails?.pickupDate}</p>
                  <p><strong>Pickup Time:</strong> {order.details.pickupDetails?.pickupTime}</p>
                </>
              )}

              <div className="flex gap-4 mt-3">
                <button
                  onClick={() => navigate("/CheckoutForm", { state: { editMode: true } })}
                  className="bg-yellow-500 text-white px-3 py-1 rounded hover:bg-yellow-600"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(order.details._id)}
                  className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
                >
                  Delete
                </button>
              </div>
            </div>
          )}
        </div>
      ))}
      <div className="mt-6 text-center">
        <button
          onClick={() => navigate("/OrderSupportChat")}
          className="bg-green-500 text-white px-6 py-3 rounded-md hover:bg-green-600"
        >
          Go to Order Chatbot
        </button>
      </div>
    </div>
  );
};

export default OrderList;


// import React, { useEffect, useState } from "react";
// import axios from "axios";
// import { useNavigate } from "react-router-dom";

// const OrderStatusBadge = ({ status }) => {
//   const statusStyles = {
//     Pending: "bg-yellow-200 text-yellow-800",
//     Approved: "bg-blue-200 text-blue-800",
//     Cancelled: "bg-red-200 text-red-800",
//     handedOver: "bg-green-200 text-green-800",
//   };

//   return (
//     <span className={`px-3 py-1 rounded-full text-sm font-semibold ${statusStyles[status] || "bg-gray-300 text-gray-700"}`}>
//       {status}
//     </span>
//   );
// };

// const OrderList = () => {
//   const [orders, setOrders] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const navigate = useNavigate();

//   useEffect(() => {
//     const fetchOrders = async () => {
//       try {
//         const token = localStorage.getItem('token');
//         const response = await axios.get("http://localhost:5000/api/successorders/successOrder/all", {
//           headers: {
//             Authorization: `Bearer ${token}`,
//             'Cache-Control': 'no-cache',
//           },
//         });
//         console.log("Fetched orders:", response.data);
//         setOrders([response.data]);
//       } catch (error) {
//         console.error("Error fetching orders", error);
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchOrders();
//   }, []);

//   if (loading) return <p className="text-center text-gray-600">Loading orders...</p>;

//   if (!orders.length) return <p className="text-center text-gray-600">No orders found.</p>;

//   const getItemRoute = (item) => {
//     switch (item.itemType.toLowerCase()) {
//       case "prebuild":
//         return `/gaming-builds/${item.itemId._id}`;
//       case "product":
//         return `/shop/${item.itemId._id}`;
//       default:
//         return "/";
//     }
//   };

//   return (
//     <div className="p-4">
//       <h2 className="text-2xl font-bold mb-6">My Orders</h2>

//       {orders.map((order) => (
//         <div key={order._id} className="border rounded-lg p-4 mb-6 shadow-md">
//           <div className="flex justify-between items-center mb-2">
//             <OrderStatusBadge status={order.status} />
//             <span className="text-sm text-gray-500">
//               Ordered At: {new Date(order.createdAt).toLocaleString()}
//             </span>
//           </div>

//           <p className="text-lg font-semibold mb-2">Total: ₹{order.totalAmount}</p>

//           <div className="mt-3">
//             <strong>Items:</strong>
//             <ul className="list-disc list-inside space-y-2 mt-1">
//               {order.items.map((item, idx) => (
//                 <li key={idx} className="flex justify-between items-center">
//                 <div className="flex items-center space-x-3">
//                 {item.itemId?.image && (
//                   <img
//                   src={item.itemId.image}
//                   alt="item"
//                   className="w-12 h-12 object-cover rounded"
//                   onError={(e) => (e.target.style.display = "none")}
//                 />
//               )}
//                   <span>
//                     {item.itemType}: {item.itemId?.description || "Unnamed"} x {item.quantity}
//                   </span>
//                 </div>
              
//                 {item.itemId?._id && (
//                   <button
//                     onClick={() => navigate(getItemRoute(item))}
//                     className="bg-blue-500 text-white px-3 py-1 rounded-md text-sm hover:bg-blue-600 transition-all"
//                   >
//                     View Item
//                   </button>
//                 )}
//               </li>              
//               ))}
//             </ul>
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// };

// export default OrderList;


// // import React, { useEffect, useState } from "react";
// // import axios from "axios";

// // const OrderList = () => {
// //   const [orders, setOrders] = useState([]);
// //   const [loading, setLoading] = useState(true);

// //   useEffect(() => {
// //     const fetchOrders = async () => {
// //       try {
// //         const token = localStorage.getItem('token');
// //         const response = await axios.get("http://localhost:5000/api/successorders/successOrder/all", {
// //           headers: {
// //             Authorization: `Bearer ${token}`, // if using JWT
// //             'Cache-Control': 'no-cache', // Prevent caching
// //           },
// //         });
// //         console.log("Fetched orders:", response.data);
// //         setOrders(response.data);
// //       } catch (error) {
// //         console.error("Error fetching orders", error);
// //       } finally {
// //         setLoading(false);
// //       }
// //     };

// //     fetchOrders();
// //   }, []);

// //   if (loading) return <p>Loading...</p>;

// //   return (
// //     <div className="p-4">
// //       <h2 className="text-xl font-bold mb-4">My Orders</h2>

// //       {orders ? (
// //   <div key={orders._id} className="border rounded-lg p-4 mb-4 shadow">
// //     <p><strong>Status:</strong> {orders.status}</p>
// //     <p><strong>Total:</strong> ₹{orders.totalAmount}</p>
// //     <p><strong>Ordered At:</strong> {new Date(orders.createdAt).toLocaleString()}</p>
// //     <div className="mt-2">
// //       <strong>Items:</strong>
// //       <ul className="list-disc list-inside">
// //         {orders.items.map((item, idx) => (
// //           <li key={idx}>
// //             {item.itemType}: {item.itemId?.name || "Unnamed"} x {item.quantity}
// //           </li>
// //         ))}
// //       </ul>
// //     </div>
// //   </div>
// // ) : (
// //   <p>No orders found.</p>
// // )}
// //     </div>
// //   );
// // };

// // export default OrderList;
