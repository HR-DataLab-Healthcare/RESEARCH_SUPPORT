# MSSQL Docker Setup for Nursing Database (NANDA/NIC/NOC) UBUNTU VM

This documentation provides a comprehensive guide to setting up a SQL Server 2025 environment using Docker on an **Ubuntu VM (145.38.192.63)** and populating it with nursing production data for use in LLM-based applications like Langflow.

---

## 🚀 Overview

This project automates the deployment of a **Microsoft SQL Server 2025** container on an Ubuntu Linux environment. It includes specific steps to resolve "name in use" conflicts, ensure container persistence through reboots, and handle the transition from Windows-style `.sql` scripts to Linux-based storage.

## 🛠️ Prerequisites

### 1. Langflow Connectivity Setup

Before connecting Langflow to MSSQL, you must install the necessary system dependencies and the `pymssql` driver inside your Langflow container.

```bash
# 1. Install system dependencies required to build pymssql
docker exec -u root -it langflow apt-get update
docker exec -u root -it langflow apt-get install -y build-essential python3-dev libsybdb5 freetds-dev

# 2. Install the Python package
docker exec -it langflow pip install pymssql

```

---

## 📦 Database Initialization

### 1. Remove Existing Containers

To avoid naming conflicts, remove any previous instances of the SQL server:

```bash
docker rm -f mssql_server

```

### 2. Launch the SQL Server 2025 Container

We use the `--restart always` flag to ensure the database starts automatically if the VM reboots.

* **Local Directory:** `~/NANDA` (The `.sql` file must be stored here).
* **Container Path:** `/scripts`.

```bash
docker run -e "ACCEPT_EULA=Y" \
   -e "MSSQL_SA_PASSWORD=YourStrongPassword123!" \
   -p 1433:1433 --name mssql_server \
   -v ~/NANDA:/scripts \
   --restart always \
   -d mcr.microsoft.com/mssql/server:2025-latest

   ==========================================================================================
   Breakdown of the Bash shell command:
         -e "ACCEPT_EULA=Y": Accepts the End-User License Agreement.
         -e "MSSQL_SA_PASSWORD=...": Sets the system administrator SA password.
         -p 1433:1433: Maps the container's port 1433 to your local machine's port 1433.
         -v flag makes your SQL file available inside the container 
            at the path /scripts/MSSQL-e1.0-Productie-NNNdb2021-v1.1.sql
         --name mssql_server: Assigns a friendly name to the container.
         -d: Runs the container in the background (detached mode).
   ==========================================================================================
```
### 3. Verify the Environment

Ensure the container is running and the volume mount is active:

```bash
# Check container status
docker ps

# Verify volume mount paths
docker inspect mssql_server | grep -A 5 Mounts

# Confirm the SQL script is visible inside the container
docker exec -it mssql_server ls /scripts
# Expected output: MSSQL-e1.0-Productie-NNNdb2021-v1.1.sql

```

---

## 🏗️ Data Import Workflow (The "Clean Slate" Import)

Because standard scripts often contain hardcoded Windows paths (e.g., `C:\Program Files\...`), we must manually define the database structure using Linux-native paths before importing data.

### Step A: Pre-create Database Shell

Create the database files within the container’s internal Linux directory:

```bash
docker exec -it mssql_server /opt/mssql-tools18/bin/sqlcmd \
   -S localhost -U sa -P "YourStrongPassword123!" -C \
   -Q "CREATE DATABASE [prod_NNNdb2021v2] ON PRIMARY (NAME = N'prod_NNNdb2021v2', FILENAME = N'/var/opt/mssql/data/prod_NNNdb2021v2.mdf') LOG ON (NAME = N'prod_NNNdb2021v2_log', FILENAME = N'/var/opt/mssql/data/prod_NNNdb2021v2_log.ldf');"

```

### Step B: Execute Full Data Script

Populate the tables. **Note:** This process may take several minutes to complete.

```bash
docker exec -it mssql_server /opt/mssql-tools18/bin/sqlcmd \
   -S localhost -U sa -P "YourStrongPassword123!" -C \
   -d prod_NNNdb2021v2 -i /scripts/MSSQL-e1.0-Productie-NNNdb2021-v1.1.sql

```

### Step C: Verify Data Integrity

Confirm the tables (NANDA, NIC, NOC, etc.) were created successfully:

```bash
docker exec -it mssql_server /opt/mssql-tools18/bin/sqlcmd \
   -S localhost -U sa -P "YourStrongPassword123!" -C \
   -d prod_NNNdb2021v2 -Q "SELECT name FROM sys.tables;"

```

*Expected Result: 28 rows affected, listing tables such as `ref_NANDA_diagnose`, `ref_NIC_interventie`, and `ref_NOC_zorgresultaat`.*

---

## 🔗 Langflow Integration

Use the following connection strings depending on where your Langflow instance is located.

### Connection URI Table

| Scenario | Connection String |
| --- | --- |
| **Langflow on the same VM** | `mssql+pymssql://sa:YourStrongPassword123!@172.17.0.1:1433/prod_NNNdb2021v2` |
| **Langflow on a different machine** | `mssql+pymssql://sa:YourStrongPassword123!@145.38.192.63:1433/prod_NNNdb2021v2` |

---



