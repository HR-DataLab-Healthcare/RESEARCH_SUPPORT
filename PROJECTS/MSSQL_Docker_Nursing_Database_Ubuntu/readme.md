

# MSSQL Docker Setup for Nursing Database (NANDA/NIC/NOC) WINDOWS 11

This documentation provides a comprehensive guide to setting up a SQL Server 2025 environment using Docker on Windows 11 and populating it with nursing production data for use in LLM-based applications like Langflow.

---

## 🚀 Overview

This project automates the deployment of a **Microsoft SQL Server 2025** container on Windows 11. 

It includes a specific workflow to handle the transition from Windows-style `.sql` scripts (with hardcoded file paths) to the Linux-based filesystem used inside the Docker container.

## 🛠️ Prerequisites

* **Windows 11** with Docker Desktop installed.
* **Python/Langflow Environment**

To use the database with Langflow, install the driver:
```bash
pip install pymssql

```

---

## 📦 Database Initialization

### 1. Pull the SQL Server 2025 Image

Open PowerShell and download the latest official Microsoft image:

```powershell
docker pull mcr.microsoft.com/mssql/server:2025-latest

```

### 2. Launch the Container

We will mount your local data directory to the container so the `.sql` script is accessible.

* **Local Directory:** `E:\CODING_STUFF\mysql-docker\data` <br> The .sql script called MSSQL-e1.0-Productie-NNNdb2021-v1.1.sql <br> must be stored at `E:\CODING_STUFF\mysql-docker\data`

* **Container Path:** `/scripts`

```powershell
docker run -e "ACCEPT_EULA=Y" `
   -e "MSSQL_SA_PASSWORD=YourStrongPassword123!" `
   -p 1433:1433 --name mssql_server `
   -v "E:\CODING_STUFF\mysql-docker\data:/scripts" `
   -d mcr.microsoft.com/mssql/server:2025-latest

   Breakdown of the Powershell command:
         -e "ACCEPT_EULA=Y": Accepts the End-User License Agreement.
         -e "MSSQL_SA_PASSWORD=...": Sets the system administrator (sa) password.
         -p 1433:1433: Maps the container's port 1433 to your local machine's port 1433.
         -v flag makes your SQL file available inside the container at the path /scripts/MSSQL-e1.0-Productie-NNNdb2021-v1.1.sql
         --name mssql_server: Assigns a friendly name to the container.
         -d: Runs the container in the background (detached mode).

```

### 3. Verify Container & Volume

Check if the container is running and the volume is correctly mapped:

```powershell
# Verify status
docker ps
    =============================================================================================================================================================================================
    The "STATUS" column should say Up (see below):

                (base) PS E:\CODING_STUFF\mysql-docker> docker ps
                CONTAINER ID   IMAGE                                        COMMAND                  CREATED        STATUS        PORTS                                         NAMES
                d3b5507486fa   mcr.microsoft.com/mssql/server:2025-latest   "/opt/mssql/bin/laun…"   22 hours ago   Up 22 hours   0.0.0.0:1433->1433/tcp, [::]:1433->1433/tcp   mssql_server
    =============================================================================================================================================================================================

# Verify the .sql file exists inside the container
docker exec -it mssql_server ls /scripts


    =============================================================================
      "Mounts": 
                "Type": "bind"
                "Source": "E:\\CODING_STUFF\\mysql-docker\\data"
                "Destination": "/scripts"
                "Mode": ""
    =============================================================================

    Note: the .sql file has the folling details:
      ==========================================================================================
          Directory: E:\CODING_STUFF\mysql-docker\data

      Mode                 LastWriteTime         Length Name
      ----                 -------------         ------ ----
      -a---          11/12/2025  9:44 AM       35096292 MSSQL-e1.0-Productie-NNNdb2021-v1.1.sql
      ==========================================================================================

# Verify the actual database
docker exec -it mssql_server ls /scripts

      ==========================================================================================
                              -e1.0-Productie-NNNdb2021-v1.1.sql
      ==========================================================================================
```

---

## 🏗️ Data Import Workflow

Because standard `.sql` exports often contain Windows file paths (e.g., `C:\Program Files\...`), we must manually initialize the database shell using Linux paths before running the full script.

### Step A: Pre-create Database Shell

This command creates the database files <br> inside the Docker's container's native Linux path (`/var/opt/mssql/data/`).

```powershell
docker exec -it mssql_server /opt/mssql-tools18/bin/sqlcmd `
    -S localhost -U sa -P "YourStrongPassword123!" -C `
    -Q "CREATE DATABASE [prod_NNNdb2021v2] ON PRIMARY (NAME = N'prod_NNNdb2021v2', FILENAME = N'/var/opt/mssql/data/prod_NNNdb2021v2.mdf') LOG ON (NAME = N'prod_NNNdb2021v2_log', FILENAME = N'/var/opt/mssql/data/prod_NNNdb2021v2_log.ldf');"

```

### Step B: Execute Full Script

Run the production script to populate the tables (NANDA, NIC, NOC). <br> Note that the process may take several minutes.

```powershell
docker exec -it mssql_server /opt/mssql-tools18/bin/sqlcmd `
    -S localhost -U sa -P "YourStrongPassword123!" -C `
    -d prod_NNNdb2021v2 -i "/scripts/MSSQL-e1.0-Productie-NNNdb2021-v1.1.sql"

        Once the script finishes you should see (can take up to  a few minutes):
        ==================================================================
                  Changed database context to 'master'.
        ==================================================================

Summary:
  ================================================================================================================
  Volume Mapping: You linked E:\CODING_STUFF\mysql-docker\data to /scripts 
  inside the container.

  Path Translation: You bypassed the Windows-style file paths inside your SQL script
  by manually defining the .mdf and .ldf locations in a Linux format.

  Database Ready: You now have a working SQL Server 2025 instance 
  containing the production nursing database.
  ================================================================================================================
```

---

## 🔗 Langflow Integration

To connect this database to a **Langflow SQL Agent** or **SQL Node**, use the following connection URI.

**Langflow SQL Connection URI:**

```text
mssql+pymssql://sa:YourStrongPassword123!@localhost:1433/prod_NNNdb2021v2

```

> **Note:** If you are running Langflow inside its own Docker container, replace `localhost` with `host.docker.internal`.





## 🧪 Connection Test Script
Here is a Python test script you can use to verify that your Dockerized SQL Server is reachable and the data is accessible before you plug it into Langflow.

Save this file as `test_db_connection.py` and run it from your local terminal.

```python
import pymssql

# Connection details
server = 'localhost'
user = 'sa'
password = 'YourStrongPassword123!'
database = 'prod_NNNdb2021v2'

try:
    print(f"Connecting to {database}...")
    conn = pymssql.connect(server, user, password, database)
    cursor = conn.cursor()
    
    # Simple query to verify tables exist
    cursor.execute("SELECT TOP 5 name FROM sys.tables")
    print("\nSuccessfully connected! Tables found in database:")
    for row in cursor:
        print(f" - {row[0]}")
        
    conn.close()
except Exception as e:
    print(f"\n❌ Connection failed: {e}")

```

---

## 🧱 Langflow SQL Agent Configuration

When you move into Langflow to build your agent, use the configuration below for the **SQL Database** or **SQL Agent** node. This setup allows the LLM to "see" your nursing data schema and answer natural language questions about NANDA, NIC, or NOC.

| Field | Value |
| --- | --- |
| **Dialect** | `mssql` |
| **Driver** | `pymssql` |
| **Username** | `sa` |
| **Password** | `YourStrongPassword123!` |
| **Host** | `localhost` (or `host.docker.internal` if Langflow is in Docker) |
| **Port** | `1433` |
| **Database** | `prod_NNNdb2021v2` |

---

### 🔗 Langflow SQLAlchemy URI

If your node requires a single string URI, use this format:
`mssql+pymssql://sa:YourStrongPassword123!@localhost:1433/prod_NNNdb2021v2`

Would you like me to help you write a specific prompt for the Langflow Agent to help it understand the relationships between the NANDA, NIC, and NOC tables?