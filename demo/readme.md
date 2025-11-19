# HappyMedicalAI Demo Repository

| Introduction Page     | Demo Page            |
| ---------------------- | --------------------- |
| ![](./media/intro.png) | ![](./media/demo.png) |

<https://github.com/hibetterheyj/HappyMedicalAI/tree/master/demo>

| Chapter | Case Topic                                  | Core Technology Keywords       |
| ------ | ------------------------------------------- | ------------------------------ |
| Chapter 2 | Mainstream Large Models: Medical Auxiliary Triage & Science Popularization | Prompt Engineering             |
| Chapter 3 | General Medical Large Models: RAG-based Weight Management Dietary Recommendations | Context Engineering            |
| Chapter 4 | Professional Medical Large Models: Dental Medicine Auxiliary Diagnosis | Model Fine-Tuning, Reinforcement Learning |

## Quick Start

```bash
# Create a virtual environment
conda create -n rag python=3.12
conda activate rag
pip install -r requirements.txt

# Pull required models (local Ollama deployment)
ollama pull bge-m3:567m  # Embedding model
ollama pull deepseek-r1:1.5b  # Chat model
ollama pull qwen2.5vl:3b
ollama pull qwen2.5vl:7b
ollama pull gemma3:4b
ollama pull gemma3:1b
ollama pull llama3.2:3b
ollama pull llama3.2:1b

# Launch the application
streamlit run app.py
```

## Model Configuration

```yaml
# Sample config.yaml
# API configuration file, distinguishing chat models and embedding models from different providers
# Future plans include supporting rerank models and distinguishing between single-modal and multi-modal models
ollama:
  base_url: "http://localhost:11434"
  chat_models:
    - name: "deepseek-r1:1.5b"
      default: true
  embedding_models:
    - name: "bge-m3:567m"
      default: true

qwen:
  api_key: "" # Please enter your API key
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  chat_models:
    - name: "Qwen3-235B-A22B"
      default: true
    - name: "Qwen3-72B"
    - name: "Qwen2.5-VL-7B-Instruct"
    - name: "Qwen2-VL-72B"
  embedding_models:
    - name: "Qwen3-Embedding-8B"
      default: true
```

## Project Structure

- `assets/`: Static assets directory
  - `smed_interaction/`: Medical interaction visualization resources
- `demos/`: Code for each demo module
- `core/`: Core function modules (model management, knowledge processing)
- `app.py`: Application entry point
