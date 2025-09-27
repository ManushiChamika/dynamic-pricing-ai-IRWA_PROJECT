import cron from 'node-cron';
import PettyCash from '../../models/Finance/PettyCash'; 
import Transaction from '../../models/Finance/Transaction';
// Run job on last day of month at 11:59 PM
cron.schedule('59 23 28-31 * *', async () => {
    try {
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setDate(now.getDate() + 1);

        if (tomorrow.getDate() === 1) { // It’s the last day of the month
            const currentMonth = now.getMonth();
            const currentYear = now.getFullYear();

            const pettyCashRecords = await PettyCash.find({
                date: {
                    $gte: new Date(currentYear, currentMonth, 1),
                    $lt: new Date(currentYear, currentMonth + 1, 1),
                }
            });

            const total = pettyCashRecords.reduce((sum, record) => sum + Number(record.amount), 0);

            // Insert into Transaction
            await Transaction.create({
                amount: total,
                type: "Expense",
                category: "Petty cash expense",
                // date: new Date(),
                description: `Total Petty Cash for ${now.toLocaleString('default', { month: 'long' })}`,
            });

            console.log("Monthly petty cash total moved to transactions successfully!");
        }
    } catch (error) {
        console.error("Error moving petty cash to transactions:", error);
    }
});
