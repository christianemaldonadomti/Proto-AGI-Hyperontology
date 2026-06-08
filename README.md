# Proto-AGI Hyperontology Engine

**Author:** Christian Efraín Maldonado-Sifuentes (christianemaldonadomti)

A computationally sustainable, local architecture for **Proto-AGI loops**, utilizing mathematical hyperontologies and Mixture of Experts (MoE) LLMs for $n$-ary topological reasoning.

This repository contains the source code, semantic extraction pipeline, and WebGL visualization frontend supporting the research: *"Computational Architectures for Proto-AGI: Integrating Local LLMs and Mathematical Hyperontologies for Topological Reasoning."*

## 🧠 Overview

Traditional Knowledge Graphs (KGs) rely on binary edges that fail to capture complex multidimensional semantics, making them vulnerable to logical poisoning. This project replaces standard KGs with **Mathematical Hyperontologies** based on Set Theory, enabling a single logical relation to bind an arbitrary set of concepts simultaneously.

Built under the principles of **GreenAGI**, the extraction pipeline bypasses cloud dependencies. It relies entirely on local inference via `intuyt:macro` (a fine-tuned Qwen3 MoE model utilizing only 3B active parameters) to extract, sanitize, and compile unstructured text into a deterministic, queryable $n$-ary graph structure.

## ⚙️ System Architecture

The workflow is modular and divided into four primary layers:

1. **Storage & I/O:** Manages raw text inputs and serialized JSON checkpoints.
2. **Data Partitioning:** Implements greedy token-bounded partitioning to respect strict LLM context windows.
3. **Local Cognitive Layer:** Executes inference via `intuyt:macro` and applies deterministic regex heuristics for JSON sanitization.
4. **Semantic Assembly:** Resolves topological duplications and merges local subgraphs into the global hyperontology using Set Theory.

## 🚀 Repository Structure

* `extractor.py`: Parses unstructured text, enforces BPE token limits, and interfaces with the local inference engine.
* `semantic_assembler.py`: Manages prompt constraints and iterative generation loops.
* `convert.py`: Serializes dictionaries into a hyper-optimized JSON schema, performing topological reification.
* `reader-math.php`: The PHP/WebGL frontend utilizing 3D Force-Directed Graphs to visualize local subgraphs dynamically.
* `hiperontologia_final.json`: The compiled structural payload.

## 💻 Installation & Usage

### Prerequisites

* Python 3.10+
* [Ollama](https://www.google.com/search?q=https://ollama.ai/) running locally with the `intuyt:macro` model.
* A local web server (Apache/Nginx) with PHP 8.0+ for the visualization module.

### Running the Pipeline

1. Clone the repository:
```bash
git clone https://github.com/christianemaldonadomti/Proto-AGI-Hyperontology.git
cd Proto-AGI-Hyperontology

```


2. Install dependencies:
```bash
pip install requests tiktoken

```


3. Execute the extraction:
```bash
python extractor.py

```


4. Move the resulting `hiperontologia_final.json` to your web server and access `reader-math.php`.

## 🔭 Visualization

Rendering a 20,000+ node hyperontology globally causes client-side WebGL overflow. Our frontend solves this via **Topological Bounding**, selectively rendering a local subgraph around a chosen semantic hub to maintain a fluid 60 FPS interaction rate.

*Live instance for peer review:* [trai-l.com/hyperonto/reader-math.php](https://trai-l.com/hyperonto/reader-math.php)

## 📜 License

This project is licensed under the MIT License.
