# Polaris Kit Assembly

*A gene circuit automated design platform based on a component database.*

---

## Overview

**Polaris Kit Assembly** is a comprehensive platform that enables synthetic biology researchers and beginners to design genetic circuits in a few clicks. It consists of two core Django sub‑projects:

- **WebDataBase** – provides database APIs and business‑logic APIs for the entire platform.
- **KitAssembly** – delivers a user‑friendly web service that allows beginners to select biological parts (components, vectors, plasmids) and automatically assemble them into complete gene circuits, returning a visual circuit map.

---

## Sub‑Projects

### WebDataBase
`WebDataBase` is a Django‑based backend service that:
- Manages the component database (parts, vectors, plasmids, and their metadata).
- Exposes RESTful APIs for querying, filtering, and retrieving component information.
- Implements core business logic (e.g., assembly rules, compatibility checks) used by the frontend and the KitAssembly service.

All API endpoints are versioned and documented for easy integration.

### KitAssembly
`KitAssembly` is the end‑user web application, also built with Django. It is designed for **synthetic biology beginners** who want to design gene circuits without prior programming or bioinformatics expertise.

#### Key features:
- **Part Selection** – Browse and select one or more genetic components (promoters, CDSs, terminators, etc.) from the database.
- **Vector & Plasmid Selection** – Choose a compatible vector backbone for your assembly.
- **One‑Click Assembly** – Once parts and a vector are selected, the backend validates compatibility and assembles the circuit.
- **Visual Output** – After successful assembly, the server returns a graphical gene circuit map (e.g., SVG or PNG) that clearly shows the final construct.

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip
- PostgreSQL or SQLite (development)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/PolarisKitAssembly.git
   cd PolarisKitAssembly
