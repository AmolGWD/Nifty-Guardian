function MarketMood({ data }) {

    const getTrendColor = () => {
        if (data.market_mood === "Bullish") return "#22c55e";
        if (data.market_mood === "Bearish") return "#ef4444";
        return "#f59e0b";
    };

    return (

        <div className="card">

            <h2>🌍 Market Mood</h2>

            <table className="marketTable">

                <tbody>

                    <tr>
                        <td>Market Mood</td>
                        <td
                            style={{
                                color: getTrendColor(),
                                fontWeight: "bold"
                            }}
                        >
                            {data.market_mood}
                        </td>
                    </tr>

                    <tr>
                        <td>Trend</td>
                        <td>{data.trend}</td>
                    </tr>

                    <tr>
                        <td>Volatility</td>
                        <td>{data.volatility}</td>
                    </tr>

                    <tr>
                        <td>PCR</td>
                        <td>{data.pcr}</td>
                    </tr>

                    <tr>
                        <td>OI Bias</td>
                        <td>{data.oi_bias}</td>
                    </tr>

                </tbody>

            </table>

        </div>

    );

}

export default MarketMood;