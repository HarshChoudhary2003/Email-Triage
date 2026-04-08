# 🚀 Hugging Face Deployment Guide: Email Triage OpenEnv

Follow these steps to deploy your Environment to Hugging Face Spaces.

## 1. Create a New Space
1.  Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2.  **Space Name**: `email-triage-openenv` (or your preferred name).
3.  **License**: `mit` (recommended for open environments).
4.  **Select the Space SDK**: Choose **Docker**.
5.  **Docker Template**: Choose **Blank** (our `Dockerfile` is already in the repo).
6.  **Space Hardware**: The default **CPU Basic (Free)** is sufficient for this environment.
7.  **Visibility**: **Public** (required for most hackathon submissions).
8.  Click **Create Space**.

## 2. Upload Your Files
You can upload files directly via the browser or use Git.

### Method A: Browser Upload (Quickest)
1.  In your new Space, click on the **Files** tab.
2.  Click **Add file** -> **Upload files**.
3.  Drag and drop **all files and the `env/` folder** from your project directory.
    *   `app.py`, `inference.py`, `openenv.yaml`, `Dockerfile`, `README.md`, `requirements.txt`
    *   The entire `env/` folder (including `__init__.py`, `data.py`, `environment.py`, `tasks.py`)
4.  Add a commit message like "Initial environment commit" and click **Commit changes to main**.

### Method B: Git CLI (Recommended)
1.  **Initialize Git** in your local project folder:
    ```powershell
    git init
    git remote add origin https://huggingface.co/spaces/techharsh/email-triage-openenv
    ```
2.  **Pull existing files** (like README.md or .gitattributes if they exist in the Space):
    ```powershell
    git pull origin main
    ```
3.  **Stage and Commit** our production-ready files:
    ```powershell
    git add .
    git commit -m "Deploy Email Triage OpenEnv with graders and logic"
    ```
4.  **Push to Hugging Face**:
    *   When prompted for a username, use your Hugging Face username.
    *   **When prompted for a password, use your Access Token** (generate it at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).
    ```powershell
    git push -u origin main
    ```

## 3. Configure Secrets
The environment needs an API key to run `inference.py` and for internal logging if you use LLMs.
1.  In your Space, click on the **Settings** tab.
2.  Scroll down to **Variables and secrets**.
3.  Click **New secret** for each of these:
    *   **HF_TOKEN**: Your OpenAI API Key (or a compatible provider key).
    *   **API_BASE_URL**: `https://api.openai.com/v1` (or your provider's URL).
    *   **MODEL_NAME**: `gpt-4o-mini` (the model the agent will use).

## 4. Verify the Deployment
1.  Go back to the **App** tab. You should see "Building" and then "Running".
2.  Once "Running", you can test the health check in your browser:
    *   URL: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/health`
    *   Expected result: `{"status": "ok"}`
3.  Run `inference.py` from your local machine, changing the base URL to your Space's URL:
    ```bash
    # Note: Use your space's direct API URL (usually ends in .hf.space)
    export API_BASE_URL=https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/v1
    python inference.py
    ```

## 5. Troubleshooting
*   **Port Error**: Ensure the `Dockerfile` exposes port **7860**. (Our current one does).
*   **Module Not Found**: Ensure the `env/` folder was uploaded and contains `__init__.py`.
*   **Build Logs**: If it fails to build, check the **Logs** tab in HF for specific error messages.

---
**Good luck with your submission!** 📧🚀
