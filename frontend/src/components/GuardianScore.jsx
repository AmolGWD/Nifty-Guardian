function GuardianScore({ guardian }) {

    if (!guardian) return null;

    return (

        <div className="card">

            <h2>🧠 Guardian Confidence</h2>

            <h1 style={{ color: "#22c55e" }}>
                {guardian.confidence}%
            </h1>

            <h3>{guardian.stars}</h3>

            <hr />

            <h3>✅ Passed Rules</h3>

            {guardian.passed_rules.map((rule, index) => (

                <p key={index}>
                    {rule}
                </p>

            ))}

            <br />

            <h3>❌ Failed Rules</h3>

            {guardian.failed_rules.length === 0 ? (

                <p>None</p>

            ) : (

                guardian.failed_rules.map((rule, index) => (

                    <p key={index}>
                        {rule}
                    </p>

                ))

            )}

        </div>

    );

}

export default GuardianScore;