export const deleteOrder = async (id) => {
  try {
    console.log("Sending DELETE request for order ID:", id);

    const res = await fetch(`http://localhost:5000/api/orders/${id}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error("Server response:", errorText);
      throw new Error(`Failed to delete order: ${res.statusText}`);
    }

    const result = await res.json();
    return result;
  } catch (error) {
    console.error("Error deleting order:", error);
    return { message: "Error deleting order" };
  }
};

export const updateOrder = async (id, updatedData) => {
  if (!id) {
    console.error("Order ID is missing in updateOrder function");
    return;
  }

  try {
    if (updatedData.paymentMethod === "COD") {
      updatedData.pickupDetails = undefined;
    } else if (updatedData.paymentMethod === "Pickup") {
      updatedData.codDetails = undefined;
    }
    
    const response = await fetch(`http://localhost:5000/api/orders/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updatedData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Server response:", errorText);
      throw new Error(`Failed to update order: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error updating order:", error);
    return { message: "Error updating order" };
  }
};
