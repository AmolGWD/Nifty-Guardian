function MarketSummary({ data }) {
  return (
    <div className="card">

      <h2>📈 Live Market</h2>

      <h1>{data.symbol}</h1>

      <h1>{data.price}</h1>

      <h3
        style={{
          color: data.change >= 0 ? "#00ff88" : "#ff4444",
        }}
      >
        {data.change >= 0 ? "▲" : "▼"} {data.change}
      </h3>

      <hr />

      <table className="marketTable">

        <tbody>

          <tr>
            <td>Open</td>
            <td>{data.open}</td>
          </tr>

          <tr>
            <td>High</td>
            <td>{data.high}</td>
          </tr>

          <tr>
            <td>Low</td>
            <td>{data.low}</td>
          </tr>

          <tr>
            <td>Previous Close</td>
            <td>{data.previous_close}</td>
          </tr>

        </tbody>

      </table>

    </div>
  );
}

export default MarketSummary;