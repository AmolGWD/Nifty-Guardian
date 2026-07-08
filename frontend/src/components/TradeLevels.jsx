function TradeLevels({ data }) {

    const risk = (data.entry - data.stop_loss).toFixed(2);
    const reward = (data.target1 - data.entry).toFixed(2);

    return (

        <div className="card">

            <h2>💰 Trade Levels</h2>

            <table className="marketTable">

                <tbody>

                    <tr>

                        <td>Entry</td>

                        <td style={{ color: "#38bdf8", fontWeight: "bold" }}>
                            {data.entry}
                        </td>

                    </tr>

                    <tr>

                        <td>Stop Loss</td>

                        <td style={{ color: "#ef4444", fontWeight: "bold" }}>
                            {data.stop_loss}
                        </td>

                    </tr>

                    <tr>

                        <td>Target 1</td>

                        <td style={{ color: "#22c55e", fontWeight: "bold" }}>
                            {data.target1}
                        </td>

                    </tr>

                    <tr>

                        <td>Target 2</td>

                        <td style={{ color: "#22c55e", fontWeight: "bold" }}>
                            {data.target2}
                        </td>

                    </tr>

                    <tr>

                        <td>Risk</td>

                        <td>{risk} pts</td>

                    </tr>

                    <tr>

                        <td>Reward</td>

                        <td>{reward} pts</td>

                    </tr>

                    <tr>

                        <td>Risk : Reward</td>

                        <td style={{ fontWeight: "bold" }}>
                            1 : {(reward / risk).toFixed(2)}
                        </td>

                    </tr>

                </tbody>

            </table>

        </div>

    );

}

export default TradeLevels;