function SignalCard({ data }) {

    const getSignalColor = () => {

        switch (data.signal) {

            case "BUY CE":
                return "#22c55e";

            case "BUY PE":
                return "#ef4444";

            default:
                return "#f59e0b";
        }

    };

    const getStatusColor = () => {

        if (data.status === "Active")
            return "#22c55e";

        if (data.status === "Target 1")
            return "#38bdf8";

        if (data.status === "Target 2")
            return "#6366f1";

        if (data.status === "Stop Loss")
            return "#ef4444";

        return "#f59e0b";

    };

    return (

        <div className="card">

            <h2>🎯 Current Recommendation</h2>

            <div
                style={{
                    textAlign: "center",
                    fontSize: "42px",
                    fontWeight: "bold",
                    color: getSignalColor(),
                    marginTop: "20px",
                    marginBottom: "20px"
                }}
            >
                {data.signal}
            </div>

            <table className="marketTable">

                <tbody>

                    <tr>

                        <td>Confidence</td>

                        <td>

                            <strong>{data.confidence}%</strong>

                        </td>

                    </tr>

                    <tr>

                        <td>Signal Time</td>

                        <td>{data.timestamp}</td>

                    </tr>

                    <tr>

                        <td>Risk Reward</td>

                        <td>1 : 2</td>

                    </tr>

                    <tr>

                        <td>Status</td>

                        <td
                            style={{
                                color: getStatusColor(),
                                fontWeight: "bold"
                            }}
                        >
                            {data.status || "Active"}
                        </td>

                    </tr>

                </tbody>

            </table>

        </div>

    );

}

export default SignalCard;