
import "./App.css";

function App() {
  return (
    <div className="app">
      <nav className="navbar">
        <h2>Forensic<span>AI</span></h2>
        <p>Digital Evidence Investigation System</p>
      </nav>

      <main className="hero">
        <div className="icon">⚖️</div>

        <h1>
          AI-Powered Crime Investigation
          <br />
          & Forensic Evidence Management
        </h1>

        <p className="description">
          A centralized platform to manage digital evidence,
          maintain evidence integrity, and assist investigators
          with AI-powered analysis.
        </p>

        <div className="buttons">
          <button onClick={() => alert("Login module coming next!")}>
            Investigator Login
          </button>

          <button
            className="secondary"
            onClick={() => alert("Admin module coming next!")}
          >
            Admin Portal
          </button>
        </div>

        <div className="features">
          <div>
            <h3>SHA-256</h3>
            <p>Evidence Integrity</p>
          </div>

          <div>
            <h3>AI Analysis</h3>
            <p>Digital Evidence Review</p>
          </div>

          <div>
            <h3>Secure</h3>
            <p>Case Management</p>
          </div>
        </div>
      </main>

      <footer>
        Forensic Investigation System | Final Year Project
      </footer>
    </div>
  );
}

export default App;
