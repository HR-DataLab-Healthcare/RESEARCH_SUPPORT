### Guide to deploy a Flowise Agentflow via Hugging Face Space

<details>
<summary>(Click on to view) STEP01: Deploying Flowise AgentFlows on Hugging Face</summary>

This guide explains how to deploy Flowise on a custom-made Hugging Face Space.

### Create a new space

1.  Sign in to [Hugging Face](https://huggingface.co/login).
2.  Start creating a [new Space](https://huggingface.co/new-space) with your preferred name.
3.  Select **Docker** as Space SDK and choose **Blank** as the Docker template.
4.  Select **CPU basic ∙ 2 vCPU ∙ 16GB ∙ FREE** as Space hardware.
5.  Click **Create Space**.

### Set the environment variables

1.  Go to **Settings** of your new space and find the **Variables and Secrets** section.
2.  Click on **New variable** and add the name as `PORT` with value `7860`.
3.  Click on **Save**.
4.  (Optional) Click on **New secret**.
5.  (Optional) Fill in with your environment variables, such as database credentials, file paths, etc. You can check for valid fields in the `.env.example` [here](https://github.com/FlowiseAI/Flowise/blob/main/docker/.env.example).

### Create a Dockerfile

1.  At the **files** tab, click on button **+ Add file** and click on **Create a new file** (or **Upload files** if you prefer to).
2.  Create a file called `Dockerfile` and paste the following:

    ```Dockerfile
    #################### VERSION 02 OCT 2025 ####################
    #################### VERSION 02 OCT 2025 ####################

    ### ====> use node:20-alpine (instead of node:18-alpine)
    ### ====> use flowise=2.2.5 

    FROM node:20-alpine
    USER root

    # Arguments that can be passed at build time
    ARG FLOWISE_PATH=/usr/local/lib/node_modules/flowise
    ARG BASE_PATH=/root/.flowise
    ARG DATABASE_PATH=$BASE_PATH
    ARG SECRETKEY_PATH=$BASE_PATH
    ARG LOG_PATH=$BASE_PATH/logs
    ARG BLOB_STORAGE_PATH=$BASE_PATH/storage

    # Install dependencies
    RUN apk add --no-cache git python3 py3-pip make g++ build-base cairo-dev pango-dev chromium

    ENV PUPPETEER_SKIP_DOWNLOAD=true
    ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

    # Install Flowise globally
    RUN npm install -g flowise=2.2.5

    # Configure Flowise directories using the ARG
    RUN mkdir -p $LOG_PATH $FLOWISE_PATH/uploads && chmod -R 777 $LOG_PATH $FLOWISE_PATH

    WORKDIR /data

    CMD ["npx", "flowise", "start"]
    ```

3.  Click on **Commit file to `main`** and it will start to build your app.

When the build finishes you can click on the **App** tab to see your app running.

</details>

<details>
<summary>(Click on to view)STEP02: Deploying an Agentflow</summary>

1.  In your Flowise space, click on **Add New**.
2.  Click on **Import Chatflow** and upload the [`GA-ASSISTED-SHDG.json`](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/blob/main/PROJECTS/Generative_Agent_based_Data-Synthesis/AGENT-FLOWS/GA-ASSISTED-SHDG.json) file from this repository.
3.  Click on **Save Chatflow**.

</details>

<details>
<summary>(Click on to view)STEP03: Creating Azure OpenAI Credentials</summary>

To use Azure OpenAI models in Flowise, you need to create credentials in the Azure portal.

1.  **Create an Azure Account:** If you don't have one, sign up for a free account on the [Azure website](https://azure.microsoft.com/en-us/free/).
2.  **Create an Azure OpenAI Resource:**
    *   In the Azure portal, search for "Azure OpenAI" and create a new resource.
    *   Choose your subscription, resource group, region, and a unique name for your resource.
    *   Select a pricing tier.
3.  **Get API Key and Endpoint:**
    *   Once the resource is deployed, go to the **Keys and Endpoint** section.
    *   Copy the **Key 1** (or Key 2) and the **Endpoint** URL.
4.  **Deploy a Model:**
    *   Go to the **Model deployments** section in your Azure OpenAI resource.
    *   Click on **Create** and select a model to deploy (e.g., `gpt-35-turbo`).
    *   Give your deployment a name. This will be your **Deployment Name**.

5.  **Use Credentials in Flowise:**
    *   In Flowise, when you add an Azure OpenAI node, you will be prompted to create a new credential.
    *   Enter the **API Key**, **Endpoint**, and **Deployment Name** you obtained from the Azure portal.

</details>

### References

* Jeong, C. (2025). Beyond text: Implementing multimodal large language model-powered multi-agent systems using a no-code platform. J Intell Inf Syst. doi: [10.13088/jiis.2025.31.1.191](https://arxiv.org/pdf/2501.00750v2).

### Acknowledgements

This guide is based on the official Flowise documentation for Hugging Face deployment: [https://docs.flowiseai.com/configuration/deployment/hugging-face](https://docs.flowiseai.com/configuration/deployment/hugging-face)


