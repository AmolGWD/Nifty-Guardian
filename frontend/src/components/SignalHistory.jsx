function SignalHistory({ history }) {

    return (

        <div className="card">

            <h2>Today's Signals</h2>

            <table className="history">

                <thead>

                    <tr>

                        <th>ID</th>

                        <th>Time</th>

                        <th>Signal</th>

                        <th>Conf</th>

                        <th>Status</th>

                    </tr>

                </thead>

                <tbody>

                    {history.map((row) => (

                        <tr key={row.id}>

                            <td>{row.id}</td>

                            <td>{row.time}</td>

                            <td>

                                {row.signal === "BUY CE" && "🟢 "}
                                {row.signal === "BUY PE" && "🔴 "}
                                {row.signal === "WAIT" && "🟡 "}

                                {row.signal}

                            </td>

                            <td>{row.confidence}%</td>

                            <td>{row.status}</td>

                        </tr>

                    ))}

                </tbody>

            </table>

        </div>

    );

}

export default SignalHistory;