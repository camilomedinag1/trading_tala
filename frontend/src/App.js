import React, { useEffect, useState } from "react";
import io from "socket.io-client";
import axios from "axios";
import { Line } from "react-chartjs-2";
import "chart.js/auto";

const socket = io("http://localhost:5000");

function App() {
    const [stockPrice, setStockPrice] = useState(150);
    const [priceHistory, setPriceHistory] = useState([]);
    const [balance, setBalance] = useState(10000); // Saldo inicial
    const [stocks, setStocks] = useState(0); // Cantidad de acciones

    useEffect(() => {
        socket.on("stock_price", (data) => {
            setStockPrice(data.price);
            setPriceHistory((prev) => [...prev.slice(-49), data.price]);
        });

        return () => socket.off("stock_price");
    }, []);

    const buyStock = async () => {
        const token = localStorage.getItem("token"); // JWT guardado
        try {
            const res = await axios.post(
                "http://localhost:5000/api/stock/buy",
                { quantity: 1 },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setBalance(res.data.balance);
            setStocks(res.data.stocks.AAPL || 0);
        } catch (err) {
            alert(err.response.data.message);
        }
    };

    const sellStock = async () => {
        const token = localStorage.getItem("token");
        try {
            const res = await axios.post(
                "http://localhost:5000/api/stock/sell",
                { quantity: 1 },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setBalance(res.data.balance);
            setStocks(res.data.stocks.AAPL || 0);
        } catch (err) {
            alert(err.response.data.message);
        }
    };

    const data = {
        labels: Array.from({ length: priceHistory.length }, (_, i) => i + 1),
        datasets: [
            {
                label: "AAPL Stock Price",
                data: priceHistory,
                borderColor: "blue",
                borderWidth: 2,
                fill: false,
            },
        ],
    };

    return (
        <div style={{ textAlign: "center", padding: "20px" }}>
            <h1>AAPL Stock Tracker</h1>
            <h2>Current Price: ${stockPrice.toFixed(2)}</h2>
            <h3>Balance: ${balance.toFixed(2)}</h3>
            <h3>Stocks Owned: {stocks}</h3>
            <Line data={data} />
            <br />
            <button onClick={buyStock} style={{ margin: "10px", padding: "10px", fontSize: "16px" }}>
                Buy 1 Share
            </button>
            <button onClick={sellStock} style={{ margin: "10px", padding: "10px", fontSize: "16px" }}>
                Sell 1 Share
            </button>
        </div>
    );
}

export default App;

