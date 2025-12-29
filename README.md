# Protein Folding Visualizer

An interactive web application for real-time protein structure prediction and visualization. It leverages **ESMFold** AI (Meta AI) to generate 3D structures and **3Dmol.js** for in-browser visualization.

##  Features

* **AI-Powered Prediction**: Generate PDB structures from amino acid sequences using ESMFold
* **Interactive 3D Visualization**: Rotate, zoom, and explore protein structures in real-time
* **Folding Animation**: Watch proteins fold step-by-step through the model's "recycle" iterations
* **Intuitive Controls**: Interactive slider with automatic playback (Play/Pause)

##  Prerequisites

* **Python**: Version 3.10 or higher
* **GPU** (recommended): NVIDIA graphics card with CUDA support for faster predictions

##  Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd protein-folding-visualizer
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install PyTorch

For GPU support (NVIDIA CUDA 12.x):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

For CPU only:
```bash
pip install torch torchvision torchaudio
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Verify Installation

Check GPU availability (optional):
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

##  Usage

### Start the Application
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:5000`

### How to Use

1. **Enter a Sequence**: Paste an amino acid sequence (single-letter codes: A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y)
2. **Predict Structure**: Click "Predict Structure" and wait for processing
3. **Explore the Model**: Use mouse controls to rotate and zoom the 3D structure
4. **Watch Folding**: Use the timeline slider or Play button to animate the folding process

## 📁 Project Structure
```
protein-folding-visualizer/
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Frontend interface
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   └── js/
│       └── main.js       # Client-side logic
└── README.md             # This file
```



##  Technologies

* **Backend**: Flask (Python)
* **AI Model**: ESMFold (Meta AI)
* **3D Rendering**: 3Dmol.js
* **Deep Learning**: PyTorch with CUDA support
