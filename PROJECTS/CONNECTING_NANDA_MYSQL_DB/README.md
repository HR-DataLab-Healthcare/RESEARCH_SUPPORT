# Connecting Langflow to MySQL: A Step‑by‑Step Guide for Data Scientists

This document walks you through verifying and configuring a MySQL connection for Langflow running in a Docker container on an Ubuntu VM. It covers:

1. Writing a small Python script to test the connection URI.
2. Creating or updating a MySQL user password via SSH and the mysql client.
3. Installing the required Python package (`pymysql`) inside the Langflow Docker container.
4. Configuring the Langflow SQL Agent (or SQL) component with the correct URI.

***

## Prerequisites

- Access to the Ubuntu VM hosting Langflow (IP: `145.38.192.63`) via SSH.
- SSH access to the MySQL server (`89.200.202.74`) as the Linux user `rob`.
- Docker running Langflow (container name/image: `langflow_docker-langflow`).
- The target MySQL database: `res_NANDAdb2026v1`.
- Basic familiarity with the command line and Python.

***

## Step 1: Test the Connection with a Python Script

Before configuring Langflow, verify that the connection string works from the VM (or inside the container) using a simple PyMySQL script.

```python
# test_mysql_connection.py
import pymysql

try:
    conn = pymysql.connect(
        host="89.200.202.74",      # MySQL server IP
        port=3306,
        user="rob",
        password="YOUR_PASSWORD_HERE",  # <-- replace with actual password
        database="res_NANDAdb2026v1",
        connect_timeout=5
    )
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()[^0]
        print(f"✅ Connection successful! MySQL version: {version}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

**How to run**

```bash
# On the Ubuntu VM (or inside the Langflow container)
python3 test_mysql_connection.py
```

- A version string means the URI, credentials, and network path are correct.
- If you see an error, note the message—it will point to authentication, network, or driver issues.

> 💡 The PyMySQL driver is the recommended way to connect to MySQL from Python when the default `mysqldb` driver is unavailable. Langflow’s SQL component uses SQLAlchemy, which accepts a URI of the form `mysql+pymysql://...`.

***

## Step 2: Set or Update the MySQL User Password

If you cannot log in with `mysql -u rob -p`, you need to set a password for the MySQL user `rob`. Do this via SSH into the MySQL server.

```bash
# 1. SSH into the MySQL host
ssh rob@89.200.202.74

# 2. Launch the mysql client (you can log in without a password if socket auth works)
mysql
```

Once at the `mysql>` prompt, run:

```sql
-- Check current user and privileges (optional)
SELECT USER(), CURRENT_USER();
SHOW GRANTS FOR CURRENT_USER();

-- Set a new password for the current user (rob@%)
ALTER USER CURRENT_USER() IDENTIFIED BY 'YOUR_STRONG_PASSWORD_HERE';
FLUSH PRIVILEGES;   -- May require RELOAD privilege; if it fails, the change is still applied in MySQL 5.7+ for new connections

EXIT;
```

If `ALTER USER` fails due to insufficient privileges, log in as an admin user first (e.g., `sudo mysql` or using the Debian maintenance user) and then run:

```sql
ALTER USER 'rob'@'%' IDENTIFIED BY 'YOUR_STRONG_PASSWORD_HERE';
FLUSH PRIVILEGES;
```

> 🔐 In MySQL 5.7, `ALTER USER` updates the grant tables and the change takes effect for new connections without an explicit `FLUSH PRIVILEGES`. The `WITH GRANT OPTION` seen in your grants allows the user to delegate privileges.

Now test the password locally:

```bash
mysql -u rob -p
```

Enter `YOUR_STRONG_PASSWORD_HERE` when prompted. A successful login confirms the password works for TCP/IP connections.

***

## Step 3: Install the Required Python Package in Langflow’s Docker Container

Now determine the langflow CONTAINER ID

```bash
docker ps
```

```bash
rvanderwil@langflow:~$ docker ps
CONTAINER ID   IMAGE                                        COMMAND                  CREATED        STATUS                PORTS                                                                          NAMES
20a1080a6493   langflow_docker-langflow                     "python -m langflow …"   41 hours ago   Up 41 hours                                                                                          langflow
aac7058fb826   postgres:16                                  "docker-entrypoint.s…"   8 weeks ago    Up 3 days (healthy)   5432/tcp                                                                       langflow_db
19a79058fe68   traefik:v2.11                                "/entrypoint.sh --ap…"   8 weeks ago    Up 3 days             0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp   traefik
e1ebc7f85c01   mcr.microsoft.com/mssql/server:2025-latest   "/opt/mssql/bin/laun…"   2 months ago   Up 3 days             0.0.0.0:1433->1433/tcp, [::]:1433->1433/tcp                                    mssql_server
```


Langflow’s SQL Agent component needs the `pymysql` package to interpret the `mysql+pymysql://` URI. Install it inside the running Langflow container.

```bash
# 1. Find the Langflow container ID or name
docker ps
# Example output shows: CONTAINER ID   IMAGE                                COMMAND...
# 20a1080a6493   langflow_docker-langflow       "python -m langflow ..."   ...

# 2. Open a shell in the container
docker exec -it 20a1080a6493 /bin/bash   # use /bin/sh if bash is not available

# 3. Install pymysql (use pip or pip3)
pip install pymysql
# If pip is not found, install it first:
# apt-get update && apt-get install -y python3-pip
# pip3 install pymysql

# 4. Verify installation
python -c "import pymysql; print(pymysql.__version__)"
# Should output a version number, e.g., 1.1.1

# 5. Exit the container shell
exit
```

> 🐳 Installing `pymysql` ensures SQLAlchemy can create a MySQL engine when the URI specifies the `+pymysql` driver. Without this driver, Langflow throws “No module named 'pymysql’” when building the SQLAgent component.

***

## Step 4: Configure Langflow’s SQL Agent Component

With the driver installed and the password set, configure Langflow as follows:

1. Open your flow in the Langflow UI (typically at `http://<VM_IP>:7860`).
2. Add an **SQL Agent** component (or **SQL** component if you prefer raw queries).
3. In the component’s settings, set the **Database URI** field to:

```
mysql+pymysql://rob:YOUR_STRONG_PASSWORD_HERE@89.200.202.74:3306/res_NANDAdb2026v1
```

    - Replace `YOUR_STRONG_PASSWORD_HERE` with the password you set in Step 2.
    - The `mysql+pymysql://` prefix is essential; it tells SQLAlchemy to use the PyMySQL driver.
4. (Optional) In the **Query** box, enter a simple test statement:

```sql
SELECT 1 AS test;
```

5. Run the component. You should see a result table with a single row containing `1`.

If the component fails to build or throws a connection error, check the Langflow logs:

```bash
docker logs 20a1080a6493
```

Look for messages about missing modules or connection refusals.

***

## Verification

After completing the steps above, you can confirm everything works by:

- Running the Python test script from Step 1 (should print the MySQL version).
- Executing a query via the Langflow SQL Agent component (should return expected results).
- Checking that subsequent components in your flow can consume the SQL Agent’s output without errors.

***

## Troubleshooting

| Symptom | Likely Cause | Fix |
| :-- | :-- | :-- |
| `No module named 'pymysql'` when building SQLAgent | `pymysql` not installed in the Langflow container | Install `pymysql` inside the container (Step 3) |
| `Access denied for user 'rob'@'...' (using password: YES)` | Wrong password or user not allowed from the connecting host | Verify password (Step 2); ensure user `rob@%` exists and is granted privileges |
| `Can't connect to MySQL server on '89.200.202.74' (111)` | Network issue, MySQL not listening on TCP/IP, or firewall blocking port 3306 | Test with `telnet 89.200.202.74 3306`; check MySQL `bind-address` and firewall rules |
| `SSL connection is required` | Server enforces SSL but client did not provide it | Add SSL parameters to the URI or adjust MySQL server SSL requirements |
| Connection works in Python script but not in Langflow | Langflow using a different Python environment or missing driver | Ensure `pymysql` is installed in the exact container running Langflow |


***

## References

1. Langflow SQL component MySQL connection issue and fix using `mysql+pymysql://`.
2. Generic MySQL URI format and SQLAlchemy usage.
3. Connecting to MySQL/MariaDB via URI from the command line client.
4. Using PyMySQL to connect to MySQL from Python.
5. Testing SQLAlchemy connections and the effect of `ALTER USER` without `FLUSH PRIVILEGES`.

***

You now have a fully functional MySQL connection from Langflow running in Docker on your Ubuntu VM. Happy data exploration! 🚀



[^1]: https://www.geeksforgeeks.org/python/connect-to-mysql-using-pymysql-in-python/

[^2]: https://github.com/langflow-ai/langflow/issues/6982

[^3]: https://stackoverflow.com/questions/32929318/is-there-a-way-to-test-an-sqlalchemy-connection

[^4]: https://stackoverflow.com/questions/76213766/connect-to-mysql-mariadb-from-the-command-line-client-with-a-uri-connection-stri

[^5]: https://sql-machine-learning.github.io/sqlflow/doc/run_with_mysql/

