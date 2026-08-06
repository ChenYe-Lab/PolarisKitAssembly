# Polaris Kit Assembly

*A gene circuit automated design platform based on a component database.*
![Static Badge](https://img.shields.io/badge/License-GPL%203.0-blue) ![Static Badge](https://img.shields.io/badge/PolarisKitAssembly-orange?logo=github)


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
   ```

2. Set up environment variables:
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and fill in your secrets and database credentials (see comments inside the file).

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations for both projects:
   ```bash
   python manage.py migrate --settings=WebDataBase.settings
   python manage.py migrate --settings=KitAssembly.settings
   ```

5. (Optional) Load initial component data using the provided fixtures.

### Running the Servers

- **For WebDataBase** (API server):
  ```bash
  python manage.py runserver --settings=WebDataBase.settings 8001
  ```
- **For KitAssembly** (web interface):
  ```bash
  python manage.py runserver --settings=KitAssembly.settings 8000
  ```

> **Note**: The two projects can run independently, but KitAssembly relies on WebDataBase APIs. Ensure that WebDataBase is reachable (adjust `API_BASE_URL` in `.env` if needed).

---

## Configuration

All sensitive and environment‑specific settings are stored in the `.env` file. Please refer to `.env.example` for the full list of required variables, including:

- Database connection strings
- Secret keys
- API endpoints
- Debug mode flags

---

## Usage Example

1. Open `http://localhost:8000` in your browser.
2. Browse the component library and select:
   - A promoter
   - A coding sequence (CDS)
   - A terminator
   - A vector (e.g., pUC19)
3. Click **"Assemble"**.
4. Wait a moment – the backend will check compatibility and return a visual plasmid map showing the assembled circuit.

---

## Technologies

- **Django** & **Django REST Framework** – Backend APIs and web UI.
- **PostgreSQL** – Primary database.
- **Celery** (optional) – For asynchronous assembly tasks.
- **BioPython** – For sequence manipulation and validation.
- **Matplotlib / DNAplotlib** – For generating circuit diagrams.

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your improvements. Make sure to follow the coding style and include appropriate tests.


---

## License

This project is licensed under the **GNU General Public License v3.0** – see the [LICENSE](LICENSE) file for details.


---

## Contact

For questions or support, please contact the Polaris team at [polaris@example.com](mailto:polaris@example.com) or open an issue on GitHub.
