function Header() {

    return (

        <div className="topBar">

            <div>

                <h1>🛡️ NIFTY Guardian</h1>

            </div>

            <div className="statusArea">

                <div>

                    <strong>Market</strong>

                    <br />

                    <span className="green">🟢 OPEN</span>

                </div>

                <div>

                    <strong>Signal Engine</strong>

                    <br />

                    <span className="green">

                        ACTIVE

                    </span>

                </div>

                <div>

                    <strong>Last Refresh</strong>

                    <br />

                    {new Date().toLocaleTimeString()}

                </div>

            </div>

        </div>

    );

}

export default Header;