function PerformanceCard({ performance }) {

    return (

        <div className="card">

            <h2>📈 Today's Performance</h2>

            <table className="marketTable">

                <tbody>

                    <tr>
                        <td>Signals</td>
                        <td>{performance.signals}</td>
                    </tr>

                    <tr>
                        <td>Wins</td>
                        <td>{performance.wins}</td>
                    </tr>

                    <tr>
                        <td>Losses</td>
                        <td>{performance.losses}</td>
                    </tr>

                    <tr>
                        <td>Active</td>
                        <td>{performance.active}</td>
                    </tr>

                    <tr>
                        <td>Waiting</td>
                        <td>{performance.waiting}</td>
                    </tr>

                    <tr>
                        <td>Accuracy</td>
                        <td>{performance.accuracy}%</td>
                    </tr>

                    <tr>
                        <td>Risk Reward</td>
                        <td>{performance.risk_reward}</td>
                    </tr>

                    <tr>
                        <td>PnL</td>
                        <td style={{color:"#22c55e"}}>
                            {performance.pnl}
                        </td>
                    </tr>

                </tbody>

            </table>

        </div>

    );

}

export default PerformanceCard;