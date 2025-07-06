# Web App Visualization Guide

This guide provides instructions for running the web-based dashboard to visualize your Overwatch stats.

---

### **Prerequisites**

*   You must have already completed the main installation by following the `SETUP.md` guide in the project's root directory.
*   A `config.json` file must be present in the root directory of the project.

---

### **Installation**

The web application has its own set of dependencies, which are lighter than the main application's.

1.  **Navigate to the Web App Directory:**
    *   Open your terminal and change your directory to here:
        ```
        cd web_app
        ```
2.  **Install Dependencies:**
    *   Run the following command to install the necessary libraries:
        ```
        pip install -r requirements.txt
        ```

---

### **Running the Web App**

1.  **Start the Application:**
    *   From within the `web_app` directory, run:
        ```
        python app.py
        ```
2.  **View Your Dashboard:**
    *   The terminal will show that the server is running.
    *   Open your web browser and navigate to the following address to see your stats:
        [http://127.0.0.1:8050](http://127.0.0.1:8050)
