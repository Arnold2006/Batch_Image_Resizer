module.exports = {
  run: [
    // Clone the Image Resizer repository
    {
      method: "shell.run",
      params: {
        message: [
          "git clone https://github.com/Arnold2006/Image_Resizer.git app",
        ]
      }
    },
    // Install Python dependencies (only Pillow is needed — no torch, no gradio)
    {
      method: "shell.run",
      params: {
        venv: "env",      // virtual environment folder
        path: "app",      // run from inside the cloned repo
        message: [
          "uv pip install Pillow",
        ]
      }
    },
  ]
}
