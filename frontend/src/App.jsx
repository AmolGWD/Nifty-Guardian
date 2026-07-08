import { useEffect, useState } from "react";

import "./App.css";

import Header from "./components/Header";
import MarketSummary from "./components/MarketSummary";
import MarketMood from "./components/MarketMood";
import SignalCard from "./components/SignalCard";
import TradeLevels from "./components/TradeLevels";
import Indicators from "./components/Indicators";
import PerformanceCard from "./components/PerformanceCard";
import SignalHistory from "./components/SignalHistory";
import Footer from "./components/Footer";

function App() {

  const [data, setData] = useState(null);

  async function loadSignal() {

    try {

      const res = await fetch(
        "https://vigilant-xylophone-xxpw4jj75r2q5p-8000.app.github.dev/signal"
      );

      const json = await res.json();

      setData(json);

    } catch (err) {

      console.error(err);

    }

  }

  useEffect(() => {

    loadSignal();

    const timer = setInterval(loadSignal, 5000);

    return () => clearInterval(timer);

  }, []);

  if (!data) {

    return (

      <div className="loading">

        Loading NIFTY Guardian...

      </div>

    );

  }

  return (

    <div className="app">

      <Header />

      <div className="dashboard">

        {/* LEFT COLUMN */}

        <div className="left">

          <MarketSummary data={data} />

          <MarketMood data={data} />

          <SignalCard data={data} />

          <TradeLevels data={data} />

          <Indicators indicators={data.indicators} />

        </div>

        {/* RIGHT COLUMN */}

        <div className="right">

          <PerformanceCard performance={data.performance} />

          <SignalHistory history={data.history} />

        </div>

      </div>

      <Footer />

    </div>

  );

}

export default App;