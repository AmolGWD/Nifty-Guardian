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
import GuardianScore from "./components/GuardianScore";
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

      {/* Header */}

      <div className="header">

        <Header />

      </div>

      {/* Left Column */}

      <div className="market">

        <MarketSummary data={data} />

      </div>

      <div className="signal">

        <SignalCard data={data} />

      </div>

      <div className="trade">

        <TradeLevels data={data} />

      </div>

      {/* Center Column */}

      <div className="mood">

        <MarketMood data={data} />

      </div>

      <div className="guardian">

        <GuardianScore guardian={data.guardian} />

      </div>

      <div className="indicators">

        <Indicators indicators={data.indicators} />

      </div>

      {/* Right Column */}

      <div className="performance">

        <PerformanceCard performance={data.performance} />

      </div>

      <div className="history">

        <SignalHistory history={data.history} />

      </div>

      {/* Hidden Footer */}

      <div className="footer">

        <Footer />

      </div>

    </div>

  );

}

export default App;