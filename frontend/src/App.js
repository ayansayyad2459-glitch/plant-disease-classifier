import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/predict";

/* ── SVG Icon Components ────────────────────────────────────────────────── */

const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 16.5l-4-4-4 4M12 12.5v9" />
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    <path d="M16 16.5l-4-4-4 4" />
  </svg>
);

const LeafIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
    <path d="M12 8v4l2 2" />
  </svg>
);

const ShieldIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const BookIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20v2H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v15H6.5A2.5 2.5 0 0 1 4 19.5z" />
  </svg>
);

const SprayIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 8.5c0-1.4-1.1-2.5-2.5-2.5H17V5c0-1.1-.9-2-2-2h-1c-1.1 0-2 .9-2 2v1H9.5C8.1 6 7 7.1 7 8.5v11.5H3V21h18v-1.5h-4V8.5z" />
    <path d="M7 10h10" />
  </svg>
);

/* ── Translations ───────────────────────────────────────────────────────── */

const t = {
  en: {
    subtitle: "Get instant disease diagnostics for your crops.",
    upload: "Drag & Drop or Click to Upload",
    analyzing: "Analyzing...",
    classify: "Classify Disease",
    clear: "Clear",
    resultTitle: "Analysis Result",
    diseaseLabel: "Disease Identified",
    confidenceLabel: "Confidence",
    explanationTitle: "Detailed Explanation",
    pesticideTitle: "Suggested Pesticides",
    disclaimer: "Disclaimer: Always consult a local agricultural expert before applying pesticides.",
    error: "Failed to get prediction. Ensure backend & AI servers are running.",
    noFile: "Please select a file first!",
    invalidFile: "Please select a valid image file.",
  },
  hi: {
    subtitle: "अपनी फसलों के लिए तत्काल रोग निदान प्राप्त करें।",
    upload: "खींचें और छोड़ें या अपलोड करने के लिए क्लिक करें",
    analyzing: "विश्लेषण हो रहा है...",
    classify: "रोग का वर्गीकरण करें",
    clear: "साफ़ करें",
    resultTitle: "विश्लेषण परिणाम",
    diseaseLabel: "पहचाना गया रोग",
    confidenceLabel: "आत्मविश्वास",
    explanationTitle: "विस्तृत विवरण",
    pesticideTitle: "सुझाए गए कीटनाशक",
    disclaimer: "अस्वीकरण: कीटनाशकों का उपयोग करने से पहले हमेशा एक स्थानीय कृषि विशेषज्ञ से परामर्श करें।",
    error: "भविष्यवाणी प्राप्त करने में विफल। सुनिश्चित करें कि बैकएंड और एआई सर्वर चल रहे हैं।",
    noFile: "कृपया पहले एक फ़ाइल चुनें!",
    invalidFile: "कृपया एक मान्य छवि फ़ाइल चुनें।",
  },
};

/* ── Main App Component ─────────────────────────────────────────────────── */

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [language, setLanguage] = useState("en");

  const lang = t[language];

  useEffect(() => {
    if (result) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 500);
      return () => clearTimeout(timer);
    }
  }, [result]);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith("image/")) {
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    } else {
      setSelectedFile(null);
      setPreview(null);
      setError(lang.invalidFile);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError(lang.noFile);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(API_URL, formData);
      setResult(response.data);
    } catch {
      setError(lang.error);
    } finally {
      setLoading(false);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  };

  const renderPesticideLinks = (pesticides) =>
    pesticides.map((p, i) => (
      <li key={i}>
        <a href={p.link} target="_blank" rel="noopener noreferrer">
          {p.name}
        </a>
      </li>
    ));

  const details = result?.details;
  const suffix = language === "en" ? "en" : "hi";

  return (
    <div className="App">
      <header className="App-header">
        <h1>
          <span className="gradient-text">AgroScan AI</span>
        </h1>
        <p>{lang.subtitle}</p>
      </header>

      <main className="App-main">
        {!preview && (
          <div className="quote-section">
            <p className="quote-text">"The love of gardening is a seed once sown that never dies."</p>
            <p className="quote-author">— Gertrude Jekyll</p>
          </div>
        )}

        <div className="card upload-card">
          <input type="file" id="file-input" onChange={handleFileChange} accept="image/*" />

          {!preview && (
            <label htmlFor="file-input" className="upload-placeholder">
              <UploadIcon />
              <p>{lang.upload}</p>
            </label>
          )}

          {preview && (
            <div className="preview-section">
              <img src={preview} alt="Selected leaf" />
              <div className="button-group">
                <button className="classify-btn" onClick={handleUpload} disabled={loading}>
                  {loading ? lang.analyzing : lang.classify}
                </button>
                <button className="clear-btn" onClick={clearSelection} disabled={loading}>
                  {lang.clear}
                </button>
              </div>
            </div>
          )}
        </div>

        {loading && <div className="loader" />}
        {error && <p className="error-message">{error}</p>}

        {details && (
          <div className={`card result-card ${isAnimating ? "fade-in" : ""}`}>
            <h2>{lang.resultTitle}</h2>

            <div className="result-grid">
              <div className="result-item">
                <span className="result-label"><LeafIcon /> {lang.diseaseLabel}</span>
                <span className="result-value disease">{details[`disease_name_${suffix}`]}</span>
              </div>
              <div className="result-item">
                <span className="result-label"><ShieldIcon /> {lang.confidenceLabel}</span>
                <div className="confidence-bar">
                  <div className="confidence-level" style={{ width: `${Math.round(result.confidence * 100)}%` }} />
                </div>
                <span className="result-value confidence">{Math.round(result.confidence * 100)}%</span>
              </div>
            </div>

            <div className="lang-switcher">
              <button onClick={() => setLanguage("en")} className={`lang-btn ${language === "en" ? "active" : ""}`}>English</button>
              <button onClick={() => setLanguage("hi")} className={`lang-btn ${language === "hi" ? "active" : ""}`}>हिंदी</button>
            </div>

            <div className="explanation-section">
              <h3><BookIcon /> {lang.explanationTitle}</h3>
              <p>{details[`explanation_${suffix}`]}</p>
              <h3><SprayIcon /> {lang.pesticideTitle}</h3>
              <ul className="pesticide-list">
                {renderPesticideLinks(details[`pesticides_${suffix}`])}
              </ul>
            </div>

            <p className="disclaimer">{lang.disclaimer}</p>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Built by <span className="gradient-text">AYAN SAYYAD</span></p>
      </footer>
    </div>
  );
}

export default App;
