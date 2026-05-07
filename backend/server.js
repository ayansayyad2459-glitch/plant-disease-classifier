/**
 * AgroScan AI — Express API Gateway
 * Acts as a middleware between the React frontend and the Flask AI server.
 * Receives image uploads, forwards them to the Python prediction API,
 * and returns the results to the client.
 */

const express = require("express");
const cors = require("cors");
const multer = require("multer");
const axios = require("axios");
const FormData = require("form-data");

const app = express();
const PORT = process.env.PORT || 5001;
const FLASK_API_URL = process.env.FLASK_API_URL || "http://127.0.0.1:5000/predict";

app.use(cors());
app.use(express.json());

const upload = multer({ storage: multer.memoryStorage() });

app.post("/api/upload", upload.single("file"), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded." });
  }

  try {
    const formData = new FormData();
    formData.append("file", req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });

    const response = await axios.post(FLASK_API_URL, formData, {
      headers: { ...formData.getHeaders() },
    });

    res.json(response.data);
  } catch (error) {
    console.error("Prediction proxy error:", error.message);
    res.status(500).json({ error: "Failed to get a prediction from the AI model." });
  }
});

app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
});
