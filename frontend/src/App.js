import React, { useEffect, useState } from "react";
import io from "socket.io-client";
import axios from "axios";
import { Line } from "react-chartjs-2";
import "chart.js/auto";

const socket = io("http://127.0.0.1:5000");

function App() {
    // Determine if the app is in registration mode based on URL parameter
    const isRegisterMode = window.location.search.includes("register");

    // Authentication states
    const [loggedIn, setLoggedIn] = useState(false);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    // Mode selection: simulation or real-time API
    const [selectedMode, setSelectedMode] = useState("simulation");
    const [apiKey, setApiKey] = useState("");
    const [apiUrl, setApiUrl] = useState("");

    // Stock application states (active once logged in)
    const [stockPrice, setStockPrice] = useState(150);
    const [priceHistory, setPriceHistory] = useState([]);
    const [balance, setBalance] = useState(0);
    const [stocks, setStocks] = useState(0);

    useEffect(() => {
        if (loggedIn) {
            socket.on("stock_price", (data) => {
                setStockPrice(data.price);
                setPriceHistory((prev) => [...prev.slice(-49), data.price]);
            });
        }
        return () => socket.off("stock_price");
    }, [loggedIn]);

    const handleLogin = async () => {
        try {
            const payload = {
                username,
                password,
                mode: selectedMode,
            };
            if (selectedMode === "real-time") {
                payload.apiKey = apiKey;
                payload.apiUrl = apiUrl;
            }
            const res = await axios.post(
                "http://127.0.0.1:5000/api/login",
                payload,
                { withCredentials: true }
            );
            setBalance(res.data.balance);
            setStocks(res.data.stocks.AAPL || 0);
            setLoggedIn(true);
        } catch (err) {
            alert(err.response?.data?.message || "Login failed");
        }
    };

    const handleRegistration = async () => {
        // Client-side validation for registration fields
        if (!username || !password) {
            alert("Please enter both a username and a password.");
            return;
        }
        try {
            await axios.post(
                "http://127.0.0.1:5000/api/register",
                { username, password },
                { withCredentials: true }
            );
            alert("User registered successfully. Please log in.");
            window.close(); // Close registration window after successful registration
        } catch (err) {
            alert(err.response?.data?.message || "Registration failed");
        }
    };

    const handleLogout = async () => {
        try {
            await axios.post("http://127.0.0.1:5000/api/logout", {}, { withCredentials: true });
            setLoggedIn(false);
            setUsername("");
            setPassword("");
        } catch (err) {
            alert(err.response?.data?.message || "Logout failed");
        }
    };

    const buyStock = async () => {
        try {
            const res = await axios.post(
                "http://127.0.0.1:5000/api/stock/buy",
                {},
                { withCredentials: true }
            );
            setBalance(res.data.balance);
            setStocks(res.data.stocks.AAPL || 0);
        } catch (err) {
            alert(err.response?.data?.message || "Error buying stock");
        }
    };

    const sellStock = async () => {
        try {
            const res = await axios.post(
                "http://127.0.0.1:5000/api/stock/sell",
                {},
                { withCredentials: true }
            );
            setBalance(res.data.balance);
            setStocks(res.data.stocks.AAPL || 0);
        } catch (err) {
            alert(err.response?.data?.message || "Error selling stock");
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

    if (isRegisterMode) {
        return (
            <div style={{ textAlign: "center", padding: "20px" }}>
                <h1>Register</h1>
                <input
                    placeholder="Username"
                    onChange={(e) => setUsername(e.target.value)}
                />
                <br />
                <input
                    type="password"
                    placeholder="Password"
                    onChange={(e) => setPassword(e.target.value)}
                />
                <br />
                <button onClick={handleRegistration}>Register</button>
            </div>
        );
    }

    if (!loggedIn) {
        return (
            <div style={{ textAlign: "center", padding: "20px" }}>
                <h1>Login</h1>
                <input
                    placeholder="Username"
                    onChange={(e) => setUsername(e.target.value)}
                />
                <br />
                <input
                    type="password"
                    placeholder="Password"
                    onChange={(e) => setPassword(e.target.value)}
                />
                <br />
                <div style={{ margin: "10px" }}>
                    <label>
                        <input
                            type="radio"
                            value="simulation"
                            checked={selectedMode === "simulation"}
                            onChange={() => setSelectedMode("simulation")}
                        />
                        Simulated Version (Non-real-time)
                    </label>
                    <br />
                    <label>
                        <input
                            type="radio"
                            value="real-time"
                            checked={selectedMode === "real-time"}
                            onChange={() => setSelectedMode("real-time")}
                        />
                        Real-Time API Version
                    </label>
                </div>
                {selectedMode === "real-time" && (
                    <div style={{ margin: "10px" }}>
                        <input
                            placeholder="Enter your API key"
                            onChange={(e) => setApiKey(e.target.value)}
                        />
                        <br />
                        <input
                            placeholder="Enter the API URL (e.g., https://www.alphavantage.co)"
                            onChange={(e) => setApiUrl(e.target.value)}
                        />
                    </div>
                )}
                <button onClick={handleLogin}>Login</button>
                <button
                    onClick={() =>
                        window.open(
                            `${window.location.origin}?register`,
                            "_blank",
                            "width=400,height=600"
                        )
                    }
                    style={{ marginLeft: "10px" }}
                >
                    Register
                </button>
            </div>
        );
    }

    return (
        <div style={{ textAlign: "center", padding: "20px" }}>
            <button onClick={handleLogout} style={{ float: "right", margin: "10px" }}>
                Logout
            </button>
            <h1>Welcome, {username}</h1>
            <h2>AAPL Stock Tracker</h2>
            <h3>Current Price: ${stockPrice.toFixed(2)}</h3>
            <h3>Balance: ${balance.toFixed(2)}</h3>
            <h3>Stocks Owned: {stocks}</h3>
            <Line data={data} />
            <br />
            <button
                onClick={buyStock}
                style={{ margin: "10px", padding: "10px", fontSize: "16px" }}
            >
                Buy 1 Share
            </button>
            <button
                onClick={sellStock}
                style={{ margin: "10px", padding: "10px", fontSize: "16px" }}
            >
                Sell 1 Share
            </button>
        </div>
    );
}

export default App;
