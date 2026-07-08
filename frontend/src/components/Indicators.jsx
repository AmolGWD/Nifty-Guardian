function Indicators({ indicators }) {

    const Indicator = ({ name, value }) => {

        return (

            <tr>

                <td>{name}</td>

                <td
                    style={{
                        color: value ? "#22c55e" : "#ef4444",
                        fontWeight: "bold"
                    }}
                >
                    {value ? "🟢 PASS" : "🔴 FAIL"}
                </td>

            </tr>

        );

    };

    return (

        <div className="card">

            <h2>📊 Indicators</h2>

            <table className="marketTable">

                <tbody>

                    <Indicator
                        name="EMA"
                        value={indicators.EMA}
                    />

                    <Indicator
                        name="RSI"
                        value={indicators.RSI}
                    />

                    <Indicator
                        name="Supertrend"
                        value={indicators.Supertrend}
                    />

                    <Indicator
                        name="Resistance"
                        value={indicators.Resistance}
                    />

                    <Indicator
                        name="OI Confirmation"
                        value={indicators.OI}
                    />

                </tbody>

            </table>

        </div>

    );

}

export default Indicators;